from sqlalchemy import Column, Integer, ForeignKey
from database.connection import Base


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)
    пользователь_id = Column(Integer, ForeignKey("users.id"))
    услуга_id = Column(Integer, ForeignKey("chronicles.id"))
