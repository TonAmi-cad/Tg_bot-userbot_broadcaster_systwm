from aiogram import Router, F, Bot
from aiogram.types import Message
from typing import Dict
import re
from src.core.userbot import UserBot

router = Router()

@router.message(F.reply_to_message)
async def admin_reply_handler(message: Message, userbots: Dict[str, UserBot]):
    if message.reply_to_message.from_user.is_bot:
        reply_text = message.reply_to_message.text
        
        # Извлекаем данные из тега <code>
        match = re.search(r"(\d+):(.+)", reply_text.split('\n')[-1])
        
        if match:
            user_id, userbot_name = match.groups()
            user_id = int(user_id)
            
            userbot = userbots.get(userbot_name)
            
            if userbot:
                try:
                    await userbot.client.send_message(chat_id=user_id, text=message.text)
                    await message.answer("✅ Сообщение отправлено.")
                except Exception as e:
                    await message.answer(f"❌ Не удалось отправить сообщение: {e}")
            else:
                await message.answer(f"❌ Юзербот с именем '{userbot_name}' не найден.")
        else:
            # Это может произойти, если администратор ответит на другое сообщение бота
            # Можно добавить логирование или просто проигнорировать
            pass
