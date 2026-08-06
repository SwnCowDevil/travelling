from datetime import date

from pydantic import BaseModel, Field

from app.footprints.schemas import FootprintStatus


class VisitCreate(BaseModel):
    destination_id: int
    visited_on: date
    note: str | None = Field(default=None, max_length=1000)
    idempotency_key: str | None = Field(default=None, max_length=100)
    confirm_duplicate: bool = False


class VisitUpdate(BaseModel):
    visited_on: date | None = None
    note: str | None = Field(default=None, max_length=1000)
    confirm_duplicate: bool = False


class VisitDeleteRequest(BaseModel):
    replacement_status: FootprintStatus | None = None


class VisitResponse(BaseModel):
    id: int
    destination_id: int
    visited_on: date
    note: str | None
    visit_count: int


class VisitListResponse(BaseModel):
    items: list[VisitResponse]
