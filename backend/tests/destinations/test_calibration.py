import pytest
import httpx

from app.destinations.amap import AmapError, AmapPlace
from scripts.calibrate_destinations import calibrate_payload


class FakeAmapClient:
    async def search(
        self, name: str, region_code: str, province_name: str | None = None
    ) -> AmapPlace:
        if name == "无法匹配":
            raise AmapError("no POI")
        return AmapPlace(
            longitude=120.1,
            latitude=30.2,
            provider_id="poi-1",
            province_name="浙江省",
            adcode="330106",
        )


class OfflineAmapClient:
    async def search(
        self, name: str, region_code: str, province_name: str | None = None
    ) -> AmapPlace:
        request = httpx.Request("GET", "https://restapi.amap.com")
        raise httpx.ConnectError("offline", request=request)


class MustNotRunClient:
    async def search(
        self, name: str, region_code: str, province_name: str | None = None
    ) -> AmapPlace:
        raise AssertionError("verified destinations must be skipped")


class AliasOnlyClient:
    async def search(
        self, name: str, region_code: str, province_name: str | None = None
    ) -> AmapPlace:
        if name != "洪崖洞民俗风貌区":
            raise AmapError("no POI")
        return AmapPlace(106.58, 29.56, "poi-hyd", "重庆市")


@pytest.mark.asyncio
async def test_calibration_marks_only_successful_matches() -> None:
    payload = {
        "regions": [{"code": "330000", "name": "浙江省"}],
        "destinations": [
            {"name": "杭州西湖", "region_code": "330000", "latitude": 1, "longitude": 1},
            {"name": "无法匹配", "region_code": "330000", "latitude": 2, "longitude": 2},
        ]
    }

    summary = await calibrate_payload(payload, FakeAmapClient())

    assert summary == {"verified": 1, "unresolved": ["无法匹配"]}
    assert payload["destinations"][0]["coordinate_verified"] is True
    assert payload["destinations"][0]["longitude"] == 120.1
    assert payload["destinations"][1]["coordinate_verified"] is False


@pytest.mark.asyncio
async def test_calibration_aborts_on_network_failure() -> None:
    payload = {
        "regions": [{"code": "330000", "name": "浙江省"}],
        "destinations": [
            {"name": "杭州西湖", "region_code": "330000", "latitude": 1, "longitude": 1}
        ]
    }

    with pytest.raises(httpx.ConnectError):
        await calibrate_payload(payload, OfflineAmapClient())


@pytest.mark.asyncio
async def test_calibration_resumes_without_requerying_verified_places() -> None:
    payload = {
        "regions": [{"code": "330000", "name": "浙江省"}],
        "destinations": [
            {
                "name": "杭州西湖",
                "region_code": "330000",
                "latitude": 30.2,
                "longitude": 120.1,
                "coordinate_verified": True,
            }
        ],
    }

    summary = await calibrate_payload(payload, MustNotRunClient())

    assert summary == {"verified": 1, "unresolved": []}


@pytest.mark.asyncio
async def test_calibration_uses_canonical_alias_for_provider_search() -> None:
    payload = {
        "regions": [{"code": "500000", "name": "重庆市"}],
        "destinations": [
            {"name": "重庆洪崖洞", "region_code": "500000", "latitude": 1, "longitude": 1}
        ],
    }

    summary = await calibrate_payload(payload, AliasOnlyClient())

    assert summary == {"verified": 1, "unresolved": []}
