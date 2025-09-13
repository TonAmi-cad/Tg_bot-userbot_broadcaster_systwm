from src.models.repositories.repositories import (
    UserRepository,
    AdminUserRepository,
    MailingRepository,
)
from src.models.db import database
from src.core.config import load_config
from typing import List, Dict
from datetime import timedelta
import datetime


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_info: dict):
        return self.user_repository.create(data=user_info)

    def update_user(self, user_id, user_info: dict):
        return self.user_repository.update(user_id, user_info)

    def get_user(self, user_id):
        return self.user_repository.read_by_id(user_id)

    def get_all_users(self):
        return self.user_repository.read_all()

    def delete_user(self, user_id):
        return self.user_repository.delete_by_id(user_id)


class AdminUserService:
    def __init__(self, admin_user_repository: AdminUserRepository):
        self.admin_user_repository = admin_user_repository

    def create_user(self, user_info: dict):
        return self.admin_user_repository.create(data=user_info)

    def get_user(self, user_id):
        return self.admin_user_repository.read_by_id(user_id)


class MailingService:
    def __init__(self, mailing_repository: MailingRepository):
        self.mailing_repository = mailing_repository

    def create_mailing(self, mailing_data: Dict) -> any:
        return self.mailing_repository.create(mailing_data)

    def get_all_mailings(self) -> List[any]:
        return self.mailing_repository.read_all()

    def get_mailing(self, mailing_id: int) -> any:
        return self.mailing_repository.read_by_id(mailing_id)

    def get_mailing_by_name(self, name: str) -> any:
        return self.mailing_repository.get_by_name(name)

    def update_mailing(self, mailing_id: int, mailing_data: Dict):
        self.mailing_repository.update(mailing_id, mailing_data)

    def delete_mailing(self, mailing_id: int):
        self.mailing_repository.delete_by_id(mailing_id)

    def get_active_mailings(self) -> List[any]:
        return self.mailing_repository.read_all_by(is_active=True)

    def update_last_mail_date(self, mailing_id: int):
        self.mailing_repository.update_last_mail_date(mailing_id)
        
    def _parse_period(self, period_value) -> timedelta:
        if isinstance(period_value, timedelta):
            return period_value
        if isinstance(period_value, (int, float)):
            return timedelta(seconds=int(period_value))
        if isinstance(period_value, str):
            try:
                # try seconds in string
                if period_value.isdigit():
                    return timedelta(seconds=int(period_value))
                parts = [int(p) for p in period_value.split(':')]
                if len(parts) == 4:
                    days, hours, minutes, seconds = parts
                elif len(parts) == 3:
                    days, (hours, minutes, seconds) = 0, parts  # type: ignore[misc]
                elif len(parts) == 2:
                    days, hours, minutes, seconds = 0, parts[0], parts[1], 0
                elif len(parts) == 1:
                    days, hours, minutes, seconds = 0, parts[0], 0, 0
                else:
                    return timedelta(hours=1)
                return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            except Exception:
                return timedelta(hours=1)
        # default fallback
        return timedelta(hours=1)

    def get_mailings_to_run(self) -> List[any]:
        active_mailings = self.get_active_mailings()
        now = datetime.datetime.utcnow()
        mailings_to_run = []
        for mailing in active_mailings:
            if mailing.last_mail_date is None:
                mailings_to_run.append(mailing)
                continue

            period = self._parse_period(mailing.period)

            if now - mailing.last_mail_date >= period:
                mailings_to_run.append(mailing)
        return mailings_to_run
