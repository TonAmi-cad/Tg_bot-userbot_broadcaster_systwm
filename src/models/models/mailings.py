import datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    Interval,
    String,
)

from .base import Base


class Mailing(Base):
    """
    Модель для хранения настроек рассылок.

    :param id: Уникальный идентификатор рассылки.
    :param name: Название пакета рассылки (имя папки в `msg/`). Должно быть уникальным.
    :param userbot_name: Имя юзербота из `config.py`, который будет делать рассылку.
    :param chat_ids: Список ID чатов для рассылки.
    :param period: Периодичность рассылки (объект `datetime.timedelta`).
    :param is_active: Флаг активности рассылки.
    :param created_at: Дата и время создания рассылки.
    """
    __tablename__ = 'mailings'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    userbot_name = Column(String, nullable=False)
    chat_ids = Column(ARRAY(BigInteger), nullable=False)
    period = Column(Interval, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_mail_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
