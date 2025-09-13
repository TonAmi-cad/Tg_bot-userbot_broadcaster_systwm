from src.models.repositories.base_repository import BaseRepository
from src.models.models import User, AdminUser, Mailing
from typing import Callable
from contextlib import AbstractContextManager
from sqlalchemy.orm import Session


class UserRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, User)


class AdminUserRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, AdminUser)


import datetime


class MailingRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, Mailing)

    def get_by_name(self, name: str) -> Mailing | None:
        with self.session_factory() as session:
            return session.query(self.model).filter_by(name=name).first()

    def update_last_mail_date(self, mailing_id: int):
        with self.session_factory() as session:
            session.query(self.model).filter_by(id=mailing_id).update({'last_mail_date': datetime.datetime.utcnow()})
            session.commit()

