from pyrogram import Client
from src.core.config import UserbotAccount

class UserBot:
    def __init__(self, account: UserbotAccount):
        self.account = account
        self.client = Client(
            name=self.account['name'],
            api_id=self.account['api_id'],
            api_hash=self.account['api_hash'],
            phone_number=self.account['number']
        )

    async def start(self):
        await self.client.start()

    async def stop(self):
        await self.client.stop()
