from db import Base
from sqlalchemy import Column, DateTime, Integer, String, Float


class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    weight = Column(Float, nullable=True)
    hash_password = Column(String, nullable=False)
    reset_otp = Column(String(6), nullable=True)
    reset_otp_expiry = Column(DateTime, nullable=True)