import json
import asyncio

import httpx
import pytest

from app.ai.client import AIClient, InvalidAIResponse
from app.ai.schemas import RerankRequest


@pytest.mark.asyncio
async def test_temporary_503_is_retried_once(monkeypatch) -> None:
    calls = 0
    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": {"code": "upstream_busy"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    async def no_sleep(_seconds): pass
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        await AIClient("https://provider.example/v1", "sk-test", "model", http=http).test_connection()
    assert calls == 2


@pytest.mark.asyncio
async def test_non_json_503_is_retried_once(monkeypatch) -> None:
    calls = 0
    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, text="temporarily unavailable")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    async def no_sleep(_seconds): pass
    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        await AIClient("https://provider.example/v1", "sk-test", "model", http=http).test_connection()
    assert calls == 2


@pytest.mark.asyncio
async def test_model_not_found_is_not_retried() -> None:
    calls = 0
    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, json={"error": {"code": "model_not_found"}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(httpx.HTTPStatusError):
            await AIClient("https://provider.example/v1", "sk-test", "model", http=http).test_connection()
    assert calls == 1


def rerank_request() -> RerankRequest:
    return RerankRequest(
        month=4,
        origin="上海",
        candidate_ids=["hangzhou", "suzhou", "nanjing"],
        preferences=["人文", "景色"],
    )


@pytest.mark.asyncio
async def test_rerank_accepts_exactly_three_known_candidates() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer sk-test"
        payload = {
            "choices": [{"message": {"content": json.dumps({
                "items": [
                    {"destination_id": "suzhou", "reason": "园林正当时"},
                    {"destination_id": "hangzhou", "reason": "春色很好"},
                    {"destination_id": "nanjing", "reason": "人文丰富"},
                ]
            }, ensure_ascii=False)}}]
        }
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        result = await AIClient(
            base_url="https://provider.example/v1",
            api_key="sk-test",
            model="deepseek-chat",
            http=http,
        ).rerank(rerank_request())

    assert [item.destination_id for item in result.items] == [
        "suzhou", "hangzhou", "nanjing"
    ]


@pytest.mark.asyncio
async def test_rerank_rejects_unknown_destination_id() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "choices": [{"message": {"content": json.dumps({"items": [
                {"destination_id": "unknown", "reason": "invented"},
                {"destination_id": "hangzhou", "reason": "valid"},
                {"destination_id": "suzhou", "reason": "valid"},
            ]})}}]
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = AIClient("https://provider.example/v1", "sk-test", "model", http=http)
        with pytest.raises(InvalidAIResponse):
            await client.rerank(rerank_request())


@pytest.mark.asyncio
async def test_client_sends_configured_thinking_and_max_tokens() -> None:
    seen: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "{}"}}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        await AIClient(
            "https://api.deepseek.com",
            "sk-test",
            "deepseek-v4-flash",
            thinking_enabled=False,
            max_tokens=6000,
            http=http,
        ).complete_json("system", "user")

    assert seen["thinking"] == {"type": "disabled"}
    assert seen["max_tokens"] == 6000


@pytest.mark.asyncio
async def test_client_omits_thinking_when_policy_is_none() -> None:
    seen: dict = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "{}"}}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        await AIClient(
            "https://provider.example/v1",
            "sk-test",
            "model",
            thinking_enabled=None,
            max_tokens=6000,
            http=http,
        ).complete_json("system", "user")

    assert "thinking" not in seen
    assert seen["max_tokens"] == 6000
