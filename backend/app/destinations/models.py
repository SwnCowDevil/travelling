from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AdministrativeRegion(Base):
    __tablename__ = "administrative_regions"

    code: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    level: Mapped[str] = mapped_column(String(16))
    parent_code: Mapped[str | None] = mapped_column(
        ForeignKey("administrative_regions.code"),
        nullable=True,
    )


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    summary: Mapped[str] = mapped_column(String(1000), default="")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    region_code: Mapped[str] = mapped_column(ForeignKey("administrative_regions.code"))
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    suitable_months: Mapped[list[int]] = mapped_column(JSON, default=list)
    season_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    crowd_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    transport_modes: Mapped[list[str]] = mapped_column(JSON, default=list)
    climate: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    min_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.5)
    data_version: Mapped[str] = mapped_column(String(32), default="v1")

    region: Mapped[AdministrativeRegion] = relationship()
