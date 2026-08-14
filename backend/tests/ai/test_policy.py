from app.ai.policy import request_policy


def test_deepseek_official_policies_split_fast_and_deep() -> None:
    fast = request_policy("https://api.deepseek.com", "guide_fast")
    deep = request_policy("https://api.deepseek.com", "guide_deep")
    rerank = request_policy("https://api.deepseek.com", "rerank")

    assert (fast.thinking_enabled, fast.max_tokens) == (False, 6000)
    assert (deep.thinking_enabled, deep.max_tokens) == (True, 12000)
    assert (rerank.thinking_enabled, rerank.max_tokens) == (False, 1200)


def test_non_deepseek_provider_omits_vendor_thinking_field() -> None:
    policy = request_policy("https://provider.example/v1", "guide_fast")

    assert policy.thinking_enabled is None
    assert policy.max_tokens == 6000
