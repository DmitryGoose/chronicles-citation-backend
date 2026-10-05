from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from database.connection import Base


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "chronicle_id", name="one_like_per_user"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    chronicle_id = Column(
        Integer,
        ForeignKey("chronicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
