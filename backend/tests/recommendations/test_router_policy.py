from app.core.config import settings
from app.recommendations.router import build_rerank_client, get_reranker


def test_official_deepseek_rerank_disables_thinking() -> None:
    client = build_rerank_client(
        "https://api.deepseek.com", "sk-test", "deepseek-v4-pro"
    )

    assert client.thinking_enabled is False
    assert client.max_tokens == 1200
    assert client.timeout_seconds == 45


def test_system_reranker_uses_the_fast_model(db_session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_api_key", "sk-test")
    monkeypatch.setattr(settings, "ai_fast_model", "deepseek-v4-flash")

    reranker = get_reranker(user_id=999, session=db_session)

    assert reranker is not None
    assert reranker.__self__.model == "deepseek-v4-flash"
