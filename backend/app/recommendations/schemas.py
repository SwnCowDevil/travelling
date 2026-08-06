from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RecommendationCreate(BaseModel):
    origin_latitude: float = Field(ge=-90, le=90)
    origin_longitude: float = Field(ge=-180, le=180)
    origin_name: str = Field(min_length=1, max_length=100)
    month: int = Field(ge=1, le=12)
    max_distance_km: float | None = Field(default=None, gt=0)
    max_budget: int | None = Field(default=None, gt=0)
    available_days: int | None = Field(default=None, gt=0)
    include_visited: bool = False
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_seasons: list[str] = Field(default_factory=list)
    preferred_crowds: list[str] = Field(default_factory=list)
    preferred_transport: list[str] = Field(default_factory=list)
    sort_mode: Literal["recommended", "nearest", "farthest"] = "recommended"


class RecommendationItem(BaseModel):
    destination_id: int
    code: str
    name: str
    summary: str
    distance_km: float
    score: float
    reason: str | None = None


class RecommendationResponse(BaseModel):
    session_id: int
    source: Literal["ai", "rules"]
    items: list[RecommendationItem]
    has_more: bool


class RecommendationHistoryItem(BaseModel):
    session_id: int
    origin_name: str
    month: int
    shown_count: int
    source: str
    created_at: datetime


class RecommendationHistoryResponse(BaseModel):
    items: list[RecommendationHistoryItem]
