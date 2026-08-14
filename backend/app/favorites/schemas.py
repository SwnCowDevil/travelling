from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.guides.schemas import GuidePayload


class FavoriteGuideCreate(BaseModel):
    destination_id: int | None = None
    custom_destination_id: int | None = None
    generation_mode: Literal["fast", "deep"]
    source: Literal["ai", "rules"]
    payload: GuidePayload

    @model_validator(mode="after")
    def one_target(self):
        if (self.destination_id is None) == (self.custom_destination_id is None): raise ValueError("exactly one destination target is required")
        return self


class FavoriteGuideUpdate(BaseModel):
    generation_mode: Literal["fast", "deep"]
    payload: GuidePayload


class FavoriteGuideResponse(BaseModel):
    id: int
    destination_id: int | None = None
    custom_destination_id: int | None = None
    destination_type: str
    generation_mode: Literal["fast", "deep"]
    source: Literal["ai", "rules", "unknown"]
    user_edited: bool
    payload: GuidePayload
    destination_snapshot: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class FavoriteGuideListResponse(BaseModel):
    items: list[FavoriteGuideResponse]
