from dataclasses import dataclass
from environs import Env
from typing import List, Dict, Any


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: str
    url: str


@dataclass
class Interface_bot:
    token: str
    username: str
    root: List[Dict[str, Any]]
    admin: List[Dict[str, Any]]

@dataclass
class UserbotAccount:
    userbot_account: List[Dict[str, Any]]

@dataclass
class Config:
    db: DbConfig
    interface_bot: Interface_bot
    userbot_account: UserbotAccount


def load_config(path: str = ".env"):
    env = Env()
    env.read_env(path)
    return Config(
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('POSTGRES_PASSWORD'),
            user=env.str('POSTGRES_USER'),
            database=env.str('POSTGRES_DB'),
            port=env.str('DB_PORT'),
            url=env.str('DB_URL')
        ),
        interface_bot=Interface_bot(
            token=env.str('INTERFACE_BOT_TOKEN'),
            username=env.str('INTERFACE_BOT_USERNAME'),
            root=env.json('ROOT', []),
            admin=env.json('ADMIN_USERS', [])
        ),
        userbot_account=UserbotAccount(
            userbot_account=env.json('USERBOT_ACCOUNT', [])
        )
    )