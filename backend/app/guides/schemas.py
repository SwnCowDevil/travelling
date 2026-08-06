from pydantic import BaseModel, Field


class GuideGenerationRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    days: int = Field(default=2, ge=1, le=30)
    origin_name: str = Field(min_length=1, max_length=100)
    preferences: list[str] = Field(default_factory=list)


class GuidePayload(BaseModel):
    transport: list[str] = Field(min_length=1)
    weather: list[str] = Field(min_length=1)
    packing: list[str] = Field(min_length=1)
    cautions: list[str] = Field(min_length=1)
    highlights: list[str] = Field(min_length=1)
    itinerary: list[str] = Field(min_length=1)


class GuideResponse(BaseModel):
    destination_id: int
    destination_code: str
    source: str
    cache_hit: bool
    data_version: str
    payload: GuidePayload
