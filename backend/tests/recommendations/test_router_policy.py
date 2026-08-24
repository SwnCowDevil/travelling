from app.recommendations.router import build_rerank_client


def test_official_deepseek_rerank_disables_thinking() -> None:
    client = build_rerank_client(
        "https://api.deepseek.com", "sk-test", "deepseek-v4-pro"
    )

    assert client.thinking_enabled is False
    assert client.max_tokens == 1200
    assert client.timeout_seconds == 45
