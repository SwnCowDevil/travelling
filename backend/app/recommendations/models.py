from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecommendationSession(Base):
    __tablename__ = "recommendation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query: Mapped[dict[str, Any]] = mapped_column(JSON)
    candidate_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    shown_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    batches: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default="rules")
    data_version: Mapped[str] = mapped_column(String(32), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
