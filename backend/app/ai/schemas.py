from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class RerankRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    origin: str
    candidate_ids: list[str] = Field(min_length=3)
    preferences: list[str] = Field(default_factory=list)


class RerankItem(BaseModel):
    destination_id: str
    reason: str = Field(min_length=1, max_length=300)


class RerankResult(BaseModel):
    items: list[RerankItem]

    @model_validator(mode="after")
    def exactly_three_unique_items(self) -> "RerankResult":
        identifiers = [item.destination_id for item in self.items]
        if len(identifiers) != 3 or len(set(identifiers)) != 3:
            raise ValueError("AI must return exactly three unique destinations")
        return self


class AIProfileUpdate(BaseModel):
    token: str = Field(min_length=1)
    base_url: HttpUrl
    model: str = Field(min_length=1, max_length=100)
    protocol: Literal["chat_completions"] = "chat_completions"
    timeout_seconds: int = Field(default=20, ge=5, le=60)
    group_note: str | None = Field(default=None, max_length=100)

    @field_validator("base_url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("AI service URL must use HTTPS")
        return value


class AIProfileResponse(BaseModel):
    mode: Literal["system", "personal"]
    base_url: str
    model: str
    protocol: str
    timeout_seconds: int
    group_note: str | None
    masked_token: str | None
    connection_status: str
