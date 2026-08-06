from pydantic import BaseModel, ConfigDict


class DestinationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    latitude: float
    longitude: float
    region_code: str
    categories: list[str]
    suitable_months: list[int]
    summary: str
    season_tags: list[str]
    crowd_tags: list[str]
    transport_modes: list[str]
    climate: dict
    min_budget: int | None
    max_budget: int | None
    min_days: int | None
    max_days: int | None


class DestinationList(BaseModel):
    items: list[DestinationRead]
