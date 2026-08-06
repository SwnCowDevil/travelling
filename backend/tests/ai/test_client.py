import json

import httpx
import pytest

from app.ai.client import AIClient, InvalidAIResponse
from app.ai.schemas import RerankRequest


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
