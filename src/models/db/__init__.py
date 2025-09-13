from src.core.config import load_config
from .postgres_conn import Database
import os

# Указываем путь к файлу конфигурации относительно корня проекта
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
config = load_config(config_path)

database = Database(db_url=config.db.url)
