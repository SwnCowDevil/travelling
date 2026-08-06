import httpx
import pytest

from app.destinations.amap import AmapClient, AmapError


@pytest.mark.asyncio
async def test_search_returns_first_matching_poi() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["key"] == "test-key"
        assert request.url.params["keywords"] == "杭州西湖"
        assert request.url.params["city"] == "330000"
        return httpx.Response(
            200,
            json={
                "status": "1",
                "info": "OK",
                "pois": [
                    {
                        "id": "B0FFG9H9YT",
                        "name": "西湖风景名胜区",
                        "location": "120.148950,30.242310",
                        "pname": "浙江省",
                    }
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        result = await AmapClient("test-key", http=http).search("杭州西湖", "330000")

    assert result.longitude == 120.14895
    assert result.latitude == 30.24231
    assert result.province_name == "浙江省"
    assert result.adcode is None
    assert result.provider_id == "B0FFG9H9YT"


@pytest.mark.asyncio
async def test_search_rejects_empty_result() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json={"status": "1", "info": "OK", "pois": []})
    )
    async with httpx.AsyncClient(transport=transport) as http:
        with pytest.raises(AmapError, match="no POI"):
            await AmapClient("test-key", http=http).search("不存在", "330000")


@pytest.mark.asyncio
async def test_search_selects_candidate_from_expected_province() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={
                "status": "1",
                "info": "OK",
                "pois": [
                    {"id": "wrong", "name": "泰山", "location": "1,2", "pname": "广东省"},
                    {"id": "right", "name": "泰山", "location": "117.1,36.2", "pname": "山东省"},
                ],
            },
        )
    )
    async with httpx.AsyncClient(transport=transport) as http:
        result = await AmapClient("test-key", http=http).search(
            "泰山", "370000", "山东省"
        )

    assert result.provider_id == "right"
