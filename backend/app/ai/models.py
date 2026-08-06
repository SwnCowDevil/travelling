from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIProfile(Base):
    __tablename__ = "ai_profiles"
    __table_args__ = (UniqueConstraint("user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    base_url: Mapped[str] = mapped_column(String(500))
    model: Mapped[str] = mapped_column(String(100))
    protocol: Mapped[str] = mapped_column(String(40), default="chat_completions")
    timeout_seconds: Mapped[int] = mapped_column(default=20)
    group_note: Mapped[str | None] = mapped_column(String(100), nullable=True)
    encrypted_token: Mapped[str] = mapped_column(String(2000))
    token_last_four: Mapped[str] = mapped_column(String(4))
    connection_status: Mapped[str] = mapped_column(String(20), default="ok")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
