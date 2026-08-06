from enum import StrEnum

from pydantic import BaseModel


class FootprintStatus(StrEnum):
    WANT = "want"
    VISITED = "visited"
    REVISIT = "revisit"
    AVOID = "avoid"


class StatusUpdate(BaseModel):
    status: FootprintStatus


class StatusResponse(BaseModel):
    status: FootprintStatus
    warning_code: str | None = None
