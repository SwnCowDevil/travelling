from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.guides.schemas import GuidePayload


class FavoriteGuideCreate(BaseModel):
    destination_id: int
    generation_mode: Literal["fast", "deep"]
    payload: GuidePayload


class FavoriteGuideUpdate(BaseModel):
    generation_mode: Literal["fast", "deep"]
    payload: GuidePayload


class FavoriteGuideResponse(BaseModel):
    id: int
    destination_id: int
    generation_mode: Literal["fast", "deep"]
    payload: GuidePayload
    destination_snapshot: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class FavoriteGuideListResponse(BaseModel):
    items: list[FavoriteGuideResponse]
