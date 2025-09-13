from src.core.config import load_config
from src.models.db import database
from src.models.repositories.repositories import UserRepository, AdminUserRepository, MailingRepository
from src.views.services import UserService, AdminUserService, MailingService

# Загружаем конфигурацию один раз
# Указываем путь к файлу конфигурации относительно корня проекта
import os
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
config = load_config(config_path)
admin_ids = [int(admin['id']) for admin in config.interface_bot.admin]


user_repository = UserRepository(session_factory=database.session)
user_service = UserService(user_repository=user_repository)

admin_user_repository = AdminUserRepository(session_factory=database.session)
admin_user_service = AdminUserService(admin_user_repository=admin_user_repository)

mailing_repository = MailingRepository(session_factory=database.session)
mailing_service = MailingService(mailing_repository=mailing_repository)
