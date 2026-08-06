from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

STATUS_CHECK = "status IN ('want', 'visited', 'revisit', 'avoid')"


class DestinationStatus(Base):
    __tablename__ = "destination_statuses"
    __table_args__ = (
        UniqueConstraint("user_id", "destination_id"),
        CheckConstraint(STATUS_CHECK, name="ck_destination_status_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class RegionStatus(Base):
    __tablename__ = "region_statuses"
    __table_args__ = (
        UniqueConstraint("user_id", "region_code"),
        CheckConstraint(STATUS_CHECK, name="ck_region_status_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    region_code: Mapped[str] = mapped_column(
        ForeignKey("administrative_regions.code", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
