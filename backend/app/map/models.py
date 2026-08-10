from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegionBoundary(Base):
    __tablename__ = "region_boundaries"

    region_code: Mapped[str] = mapped_column(
        ForeignKey("administrative_regions.code", ondelete="CASCADE"), primary_key=True
    )
    center_longitude: Mapped[float] = mapped_column(Float)
    center_latitude: Mapped[float] = mapped_column(Float)
    polygons: Mapped[list[list[list[float]]]] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default="amap")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
