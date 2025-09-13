import logging
import os
from datetime import timedelta, datetime
from pathlib import Path

from aiogram import Bot
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from pyrogram.types import InputMediaPhoto, InputMediaVideo

from src.models.models import Mailing
from src.core.dependencies import mailing_service, admin_ids
from src.utils.paths import get_package_dir

# Рантайм-объекты, устанавливаются из main при старте
_runtime_bot: Bot | None = None
_runtime_userbots: dict | None = None


async def send_mailing(mailing_id: int):
    """
    Отправляет одно сообщение рассылки.
    """
    # Берем ранее установленные рантайм-объекты
    bot: Bot = _runtime_bot  # type: ignore[assignment]
    userbots = _runtime_userbots or {}

    mailing = mailing_service.get_mailing(mailing_id)
    if not mailing:
        logging.error(f"Рассылка с ID {mailing_id} не найдена для отправки.")
        return

    userbot_name = mailing.userbot_name
    userbot = userbots.get(userbot_name)

    if not bot or not userbot or not userbot.client or not userbot.client.is_connected:
        error_msg = f"Юзербот {userbot_name} не найден или не активен."
        logging.error(error_msg)
        for admin_id in admin_ids:
            await bot.send_message(admin_id, f"❌ Рассылка '{mailing.name}' не удалась. {error_msg}")
        return

    # Формируем абсолютный путь к папке с медиа
    package_path = get_package_dir(mailing.name)
    
    if not os.path.isdir(package_path):
        logging.error(f"Папка с пакетом рассылки '{mailing.name}' не найдена по пути {package_path}.")
        return

    files = sorted(os.listdir(package_path))
    text_files = [f for f in files if f.lower().endswith('.txt')]

    text = ""
    if text_files:
        try:
            with open(os.path.join(package_path, text_files[0]), 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logging.error(f"Не удалось прочесть текст для рассылки '{mailing.name}': {e}")

    media_group = []
    for f in files:
        lower = f.lower()
        full_path = os.path.join(package_path, f)
        if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
            media_group.append(InputMediaPhoto(full_path))
        elif lower.endswith((".mp4", ".mov", ".mkv", ".webm")):
            media_group.append(InputMediaVideo(full_path))

    # Добавляем подпись только к первому элементу медиагруппы
    if media_group and text:
        first = media_group[0]
        if isinstance(first, InputMediaPhoto):
            media_group[0] = InputMediaPhoto(first.media, caption=text)
        elif isinstance(first, InputMediaVideo):
            media_group[0] = InputMediaVideo(first.media, caption=text)

    try:
        logging.info(f"Начало рассылки: {mailing.name} (ID: {mailing.id})")
        for chat_id_raw in mailing.chat_ids:
            # Нормализуем chat_id и готовим альтернативные варианты (для супергрупп/каналов)
            candidates: list[object] = []
            try:
                as_int = int(chat_id_raw)
                candidates.append(as_int)
                # Если это отрицательный id без префикса -100 (часто для каналов/супергрупп),
                # пробуем альтернативу с префиксом -100
                if as_int < -1000 and not str(as_int).startswith("-100"):
                    candidates.append(int("-100" + str(abs(as_int))))
            except Exception:
                # не int — оставляем строковое значение как есть (username, ссылку и т.п.)
                candidates.append(chat_id_raw)

            sent_ok = False
            last_error: Exception | None = None
            for candidate in candidates:
                try:
                    # Пробуем резолв пира заранее
                    try:
                        await userbot.client.resolve_peer(candidate)
                    except Exception:
                        await userbot.client.get_chat(candidate)

                    if media_group:
                        await userbot.client.send_media_group(candidate, media_group)
                    elif text:
                        await userbot.client.send_message(candidate, text)
                    else:
                        logging.warning(f"Пакет '{mailing.name}' пуст: нет медиа и текста")
                    sent_ok = True
                    break
                except Exception as e:
                    last_error = e

            if not sent_ok:
                logging.error(
                    f"Ошибка при отправке рассылки '{mailing.name}' в чат {chat_id_raw}: {last_error}"
                )
                for admin_id in admin_ids:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f"Ошибка при отправке рассылки '{mailing.name}' в чат {chat_id_raw}: {last_error}\n"
                            f"Юзербот: {userbot_name}"
                        ),
                    )
        mailing_service.update_last_mail_date(mailing.id)
        logging.info(
            f"Обновлён last_mail_date для рассылки '{mailing.name}' (ID: {mailing.id})"
        )
    except Exception as e:
        logging.error(f"Не удалось завершить рассылку '{mailing.name}': {e}")


def schedule_mailing_for(mailing: Mailing, scheduler: AsyncIOScheduler, now: datetime | None = None):
    """
    Планирует задания для одной рассылки с учётом правил:
    - Если created_at есть, а last_mail_date отсутствует → немедленная отправка и запуск интервала через период
    - Если прошло больше, чем period, с момента last_mail_date → немедленная отправка и следующий интервал от сейчас
    - Иначе → запуск интервала через оставшееся время до (last_mail_date + period)
    """
    if now is None:
        now = datetime.utcnow()

    if mailing.last_mail_date:
        time_since_last_mail = now - mailing.last_mail_date
        if time_since_last_mail > mailing.period:
            # Догоняющая отправка
            scheduler.add_job(
                send_mailing,
                'date',
                run_date=now + timedelta(seconds=1),
                args=[mailing.id],
                id=f"mailing_{mailing.id}_missed",
                replace_existing=True,
                misfire_grace_time=300,
            )
            interval_start = now + mailing.period
        else:
            # Запуск через оставшийся интервал
            interval_start = mailing.last_mail_date + mailing.period
    else:
        # Первая активация: created_at есть всегда (по модели), поэтому отправляем сразу
        scheduler.add_job(
            send_mailing,
            'date',
            run_date=now + timedelta(seconds=1),
            args=[mailing.id],
            id=f"mailing_{mailing.id}_first",
            replace_existing=True,
            misfire_grace_time=300,
        )
        interval_start = now + mailing.period

    scheduler.add_job(
        send_mailing,
        'interval',
        seconds=mailing.period.total_seconds(),
        start_date=interval_start,
        args=[mailing.id],
        id=f"mailing_{mailing.id}",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=300,
    )


def setup_scheduler(userbots, bot: Bot):
    """
    Настраивает и запускает планировщик.
    """
    # Импортируем config локально чтобы избежать проблем с инициализацией
    from src.core.dependencies import config
    
    jobstores = {
        'default': SQLAlchemyJobStore(url=config.db.url)
    }
    # Используем таймзону UTC, чтобы избежать несоответствий локального времени
    # и предупреждений "Run time ... was missed by X" из-за смещения.
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        timezone=utc,
        job_defaults={
            'coalesce': True,
            'misfire_grace_time': 300,
        },
    )

    # Сохраняем рантайм-объекты для send_mailing
    global _runtime_bot, _runtime_userbots
    _runtime_bot = bot
    _runtime_userbots = userbots

    active_mailings = mailing_service.get_active_mailings()
    now = datetime.utcnow()

    for mailing in active_mailings:
        if mailing.userbot_name in userbots:
            schedule_mailing_for(mailing, scheduler, now)
        else:
            logging.warning(f"Юзербот '{mailing.userbot_name}' для рассылки '{mailing.name}' не найден.")

    scheduler.start()
    return scheduler