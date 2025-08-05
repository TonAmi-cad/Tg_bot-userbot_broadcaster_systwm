from sqlalchemy import Column, String, BigInteger
from src.models.models.base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    user_name = Column(String(50), nullable=True)
    real_name = Column(String(50), nullable=True)
    phone_number = Column(String(15), nullable=True)