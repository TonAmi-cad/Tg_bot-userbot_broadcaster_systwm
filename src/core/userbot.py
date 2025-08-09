import logging
from pyrogram import Client
from src.core.config import UserbotAccount

class UserBot:
    def __init__(self, account: dict):
        self.account = account
        self.client = None

    async def start(self):
        try:
            self.client = Client(
                name=self.account['name'],
                api_id=self.account['api_id'],
                api_hash=self.account['api_hash'],
                phone_number=self.account['number']
            )
            await self.client.start()
        except Exception as e:
            logging.error(f"Failed to start userbot {self.account['name']}: {e}")
            self.client = None

    async def stop(self):
        if self.client and self.client.is_connected:
            await self.client.stop()
