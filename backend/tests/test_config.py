from app.core.config import Settings


def test_settings_have_safe_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///./data/travel.db"
    assert settings.ai_base_url == "https://www.packyapi.com/v1"
    assert settings.ai_api_key is None


def test_settings_read_environment(monkeypatch) -> None:
    monkeypatch.setenv("TRAVEL_AI_MODEL", "deepseek-chat")

    settings = Settings(_env_file=None)

    assert settings.ai_model == "deepseek-chat"
