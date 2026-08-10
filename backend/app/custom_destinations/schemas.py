from datetime import datetime

from pydantic import BaseModel, Field


class CustomDestinationCandidate(BaseModel):
    amap_poi_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(default="", max_length=500)
    region_name: str = Field(default="", max_length=200)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CustomDestinationRead(CustomDestinationCandidate):
    id: int
    created_at: datetime
    updated_at: datetime


class CustomDestinationSearchResponse(BaseModel):
    items: list[CustomDestinationCandidate]
