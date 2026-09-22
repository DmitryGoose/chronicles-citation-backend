from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from database.connection import Base


class Chronicle(Base):
    __tablename__ = "chronicles"

    id = Column(Integer, primary_key=True)
    название = Column(String(255), nullable=False)
    заголовок = Column(String(255))
    описание = Column(Text)
    статус = Column(String(20), nullable=False)
    url_изображения = Column(String(500))
    url_видео = Column(String(500))
    год_авторства = Column(Integer)
    год_начала = Column(Integer)
    дата_создания = Column(DateTime)
    создатель = Column(Integer, ForeignKey("users.id"))
    дата_формирования = Column(DateTime)
