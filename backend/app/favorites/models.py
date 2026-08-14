from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FavoriteGuide(Base):
    __tablename__ = "favorite_guides"
    __table_args__ = (UniqueConstraint("user_id", "destination_id"), UniqueConstraint("user_id", "custom_destination_id"), CheckConstraint("(destination_id IS NOT NULL) != (custom_destination_id IS NOT NULL)", name="ck_favorite_one_target"))

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[int | None] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"), nullable=True, index=True)
    custom_destination_id: Mapped[int | None] = mapped_column(ForeignKey("custom_destinations.id", ondelete="CASCADE"), nullable=True, index=True)
    destination_type: Mapped[str] = mapped_column(String(10), default="public")
    generation_mode: Mapped[str] = mapped_column(String(10))
    source: Mapped[str] = mapped_column(String(10), default="unknown")
    user_edited: Mapped[bool] = mapped_column(default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    destination_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), onupdate=func.now())
