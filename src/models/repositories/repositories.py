from src.models.repositories import BaseRepository
from src.models.models import *
from typing import Callable
from contextlib import AbstractContextManager
from sqlalchemy.orm import Session


class UserRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, User)


class ManagerUserRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, ManagerUser)


class PostPlanRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]]):
        self.session_factory = session_factory
        super().__init__(session_factory, PostPlan)

    def get_all_regular_posts(self):
        with self.session_factory() as session:
            try:
                return session.query(self.model).filter(self.model.motivation == False).all()
            except Exception as e:
                raise e

    def update_period_for_all_motivational(self, period_minutes: int):
        with self.session_factory() as session:
            try:
                session.query(self.model).filter(self.model.motivation == True).update(
                    {"period_ch": period_minutes}
                )
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def update_period_for_all_regular(self, period_hours: int):
        with self.session_factory() as session:
            try:
                session.query(self.model).filter(self.model.motivation == False).update(
                    {"period_ch": period_hours}
                )
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

