from pydantic import BaseModel


class ResolvedLocationResponse(BaseModel):
    name: str
    region_name: str
    address: str
    latitude: float
    longitude: float
    source: str
