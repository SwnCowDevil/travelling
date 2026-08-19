from math import isfinite
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GuideGenerationRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    days: int = Field(default=2, ge=1, le=15)
    origin_name: str = Field(min_length=1, max_length=100)
    preferences: list[str] = Field(default_factory=list)
    generation_mode: Literal["fast", "deep"] = "fast"
    force_refresh: bool = False


class FoodRecommendation(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=300)
    area: str = Field(min_length=1, max_length=120)
    average_price: str = Field(min_length=1, max_length=80)

    @field_validator("average_price", mode="before")
    @classmethod
    def normalize_numeric_average_price(cls, value: object) -> object:
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and value >= 0
        ):
            return f"约{value:g}元/人"
        return value


class ItineraryDay(BaseModel):
    day: int = Field(ge=1, le=15)
    theme: str = Field(min_length=1, max_length=120)
    morning: str = Field(min_length=1, max_length=500)
    afternoon: str = Field(min_length=1, max_length=500)
    evening: str = Field(min_length=1, max_length=500)
    transport: str = Field(min_length=1, max_length=300)
    caution: str = Field(min_length=1, max_length=300)

    @field_validator("transport", mode="before")
    @classmethod
    def normalize_transport_string_list(cls, value: object) -> object:
        if (
            isinstance(value, list)
            and value
            and all(isinstance(item, str) and item.strip() for item in value)
        ):
            return "；".join(item.strip() for item in value)
        return value


class GuidePayload(BaseModel):
    transport: list[str] = Field(min_length=1)
    weather: list[str] = Field(min_length=1)
    packing: list[str] = Field(min_length=8, max_length=14)
    cautions: list[str] = Field(min_length=5, max_length=8)
    highlights: list[str] = Field(min_length=5, max_length=8)
    foods: list[FoodRecommendation] = Field(min_length=4, max_length=6)
    itinerary: list[ItineraryDay] = Field(min_length=1, max_length=15)

    @field_validator("highlights", mode="before")
    @classmethod
    def normalize_highlight_objects(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        normalized: list[object] = []
        for item in value:
            if not isinstance(item, dict):
                normalized.append(item)
                continue
            name = item.get("name") or item.get("名称")
            reason = (
                item.get("reason")
                or item.get("description")
                or item.get("推荐理由")
                or item.get("推荐原因")
            )
            if not (
                isinstance(name, str)
                and name.strip()
                and isinstance(reason, str)
                and reason.strip()
            ):
                return value
            normalized.append(f"{name.strip()}：{reason.strip()}")
        return normalized

    @model_validator(mode="after")
    def require_consecutive_itinerary_days(self) -> "GuidePayload":
        days = [item.day for item in self.itinerary]
        if days != list(range(1, len(days) + 1)):
            raise ValueError("itinerary days must be consecutive and start at 1")
        return self


class GuideResponse(BaseModel):
    destination_id: int
    destination_code: str
    source: str
    cache_hit: bool
    data_version: str
    payload: GuidePayload
