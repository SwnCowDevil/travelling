import httpx
import pytest

from app.locations.amap import AmapReverseClient, AmapReverseError


def client_for(payload: dict, *, status_code: int = 200):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=payload, request=request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return AmapReverseClient("test-key", http=http), http


@pytest.mark.asyncio
async def test_reverse_prefers_first_named_poi_and_builds_region():
    payload = {
        "status": "1",
        "regeocode": {
            "formatted_address": "北京市东城区东长安街",
            "addressComponent": {
                "province": "北京市",
                "city": [],
                "district": "东城区",
            },
            "pois": [{"name": "天安门"}],
        },
    }
    client, http = client_for(payload)
    try:
        result = await client.reverse(39.9087, 116.3975)
    finally:
        await http.aclose()

    assert result.name == "天安门"
    assert result.region_name == "北京市东城区"
    assert result.address == "北京市东城区东长安街"


@pytest.mark.asyncio
async def test_reverse_falls_back_to_road_then_formatted_address():
    payload = {
        "status": "1",
        "regeocode": {
            "formatted_address": "浙江省杭州市西湖区龙井路",
            "addressComponent": {
                "province": "浙江省",
                "city": "杭州市",
                "district": "西湖区",
            },
            "pois": [],
            "roads": [{"name": "龙井路"}],
        },
    }
    client, http = client_for(payload)
    try:
        result = await client.reverse(30.2, 120.1)
    finally:
        await http.aclose()

    assert result.name == "龙井路"
    assert result.region_name == "浙江省杭州市西湖区"


@pytest.mark.asyncio
async def test_reverse_sends_required_coordinate_parameters():
    captured: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.url.params))
        return httpx.Response(
            200,
            json={
                "status": "1",
                "regeocode": {
                    "formatted_address": "北京市东城区",
                    "addressComponent": {"province": "北京市", "city": [], "district": "东城区"},
                    "pois": [],
                },
            },
            request=request,
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        await AmapReverseClient("test-key", http=http).reverse(39.9087, 116.3975)
    finally:
        await http.aclose()

    assert captured["location"] == "116.397500,39.908700"
    assert captured["extensions"] == "all"
    assert captured["radius"] == "1000"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"status": "0", "info": "INVALID_USER_KEY"},
        {"status": "1", "regeocode": []},
        {"status": "1", "regeocode": {"addressComponent": {}, "pois": []}},
    ],
)
async def test_reverse_rejects_upstream_and_malformed_payloads(payload):
    client, http = client_for(payload)
    try:
        with pytest.raises(AmapReverseError):
            await client.reverse(39.9, 116.4)
    finally:
        await http.aclose()
