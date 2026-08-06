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
