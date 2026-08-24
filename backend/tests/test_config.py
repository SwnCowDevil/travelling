from app.core.config import Settings


def test_settings_have_safe_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./data/travel.db"
    assert settings.ai_base_url == "https://api.deepseek.com"
    assert settings.ai_model == "deepseek-v4-pro"
    assert settings.ai_fast_model == "deepseek-v4-flash"
    assert settings.ai_recommendation_timeout_seconds == 45
    assert settings.ai_api_key is None
    assert settings.amap_key is None


def test_settings_read_environment(monkeypatch) -> None:
    monkeypatch.setenv("TRAVEL_AI_MODEL", "deepseek-chat")

    settings = Settings(_env_file=None)

    assert settings.ai_model == "deepseek-chat"


def test_blank_jwt_secret_uses_safe_local_default(monkeypatch) -> None:
    monkeypatch.setenv("TRAVEL_JWT_SECRET", "")

    settings = Settings(_env_file=None)

    assert settings.jwt_secret == "development-only-change-me-before-deploying"
