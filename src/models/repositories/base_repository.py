import logging
from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


class BaseRepository:

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], model):
        self.session_factory = session_factory
        self.model = model

    def read_all(self):
        with self.session_factory() as session:
            try:
                return session.query(self.model).all()
            except Exception as e:
                raise e

    def read_by_id(self, user_id: int):
        with self.session_factory() as session:
            try:
                query = session.query(self.model)
                query = query.filter(self.model.id == user_id).first()
            except Exception as e:
                raise e
            return query

    def read_by(self, **kwargs):
        with self.session_factory() as session:
            try:
                return session.query(self.model).filter_by(**kwargs).first()
            except Exception as e:
                raise e

    def read_all_by(self, **kwargs):
        with self.session_factory() as session:
            try:
                return session.query(self.model).filter_by(**kwargs).all()
            except Exception as e:
                raise e

    def create(self, data: dict):
        with self.session_factory() as session:
            try:
                existing_user = session.query(self.model).filter_by(id=data.get('id')).first()
                if existing_user:
                    return existing_user

                model = self.model(**data)
                session.add(model)
                session.commit()
                session.refresh(model)
                return model
            except Exception as e:
                session.rollback()
                raise e

    def update(self, item_id: int, data: dict):
        with self.session_factory() as session:
            try:
                session.query(self.model).filter(self.model.id == item_id).update(data)
                session.commit()
            except Exception as e:
                raise e

    def delete_by_id(self, user_id: int):
        with self.session_factory() as session:
            try:
                query = session.query(self.model).filter(self.model.id == user_id).first()
                session.delete(query)
                session.commit()
            except Exception as e:
                raise e
