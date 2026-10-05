from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text, text

from database.connection import Base


class Chronicle(Base):
    __tablename__ = "chronicles"
    __table_args__ = (
        CheckConstraint(
            "status IN ('черновик', 'опубликован', 'удален')",
            name="chronicles_status_check",
        ),
        Index(
            "one_draft_per_user",
            "creator_id",
            unique=True,
            postgresql_where=text("status = 'черновик'"),
        ),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    short_description = Column(Text)
    status = Column(String(20), nullable=False)
    image_url = Column(String(500))
    video_url = Column(String(500))
    authorship_year = Column(Integer)
    start_year = Column(Integer)
    created_at = Column(DateTime, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    published_at = Column(DateTime)
