from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


LOCAL_JWT_SECRET = "development-only-change-me-before-deploying"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TRAVEL_",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/travel.db"
    jwt_secret: str = LOCAL_JWT_SECRET
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    ai_base_url: str = "https://www.packyapi.ai/v1"
    ai_model: str = "deepseek-v4-pro"
    ai_api_key: str | None = None
    ai_guide_timeout_seconds: int = 90
    ai_encryption_key: str | None = None
    amap_key: str | None = None
    amap_secret: str | None = None
    enable_dev_auth: bool = False

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def default_blank_local_jwt_secret(cls, value: object) -> object:
        return LOCAL_JWT_SECRET if not str(value or "").strip() else value


settings = Settings()
