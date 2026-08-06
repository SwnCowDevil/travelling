from pydantic import BaseModel, Field


class RegionMapSummary(BaseModel):
    region_code: str
    name: str
    level: str
    direct_status: str | None = None
    status_counts: dict[str, int] = Field(default_factory=dict)
    visit_count: int = 0


class MapSummaryResponse(BaseModel):
    items: list[RegionMapSummary]
