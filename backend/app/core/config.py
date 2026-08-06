from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TRAVEL_",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/travel.db"
    jwt_secret: str = "development-only-change-me-before-deploying"
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    ai_base_url: str = "https://www.packyapi.com/v1"
    ai_model: str = "deepseek-chat"
    ai_api_key: str | None = None


settings = Settings()
