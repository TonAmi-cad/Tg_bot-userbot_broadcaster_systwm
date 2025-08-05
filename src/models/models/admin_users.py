from sqlalchemy import Column, String, BigInteger
from .base import Base


class AdminUser(Base):
    __tablename__ = 'admin_users'

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    name = Column(String(255), nullable=True) 