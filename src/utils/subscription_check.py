import logging
from aiogram import Bot
from src.core.config import load_config

config = load_config()


async def is_user_subscribed(bot: Bot, user_id: int) -> bool:
    """
    Check if user is subscribed to all required channels via Telegram API.
    The configuration must contain the channel 'id' (@username or numeric ID).
    """
    if not config.Aprove_bot.channel:
        logging.warning("Subscription check is active, but no channels are configured in .env file.")
        return True  # If no channels are required, allow access.

    try:
        for channel_data in config.Aprove_bot.channel:
            try:
                chat_id = channel_data["id"]
                chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if chat_member.status in ["left", "kicked"]:
                    return False
            except KeyError:
                logging.error(f"Configuration error for channel: {channel_data}. 'id' key is missing in .env.")
                return False  # Block access if config is broken
            except Exception as e:
                logging.error(f"Could not check subscription for channel_id '{channel_data.get('id')}'. Error: {e}")
                # Deny access for safety if a channel check fails.
                return False
        # If loop completes, user is subscribed to all channels.
        return True
    except Exception as e:
        logging.error(f"An unexpected error occurred during subscription check: {e}")
        return False 