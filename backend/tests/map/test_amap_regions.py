import httpx
import pytest
from sqlalchemy import select

from app.destinations.models import AdministrativeRegion, Destination
from app.map.amap import AmapDistrictClient, AmapDistrictError, AmapRegion, AmapRegionChild
from app.map.models import RegionBoundary
from app.map.service import sync_region_layer
from scripts.sync_map_regions import _assign_city_regions, run_sync


def test_fetch_region_parses_polyline_and_children() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "status": "1",
            "districts": [{
                "adcode": "510000", "name": "四川省", "level": "province",
                "center": "102.0,30.0",
                "polyline": "104.0,30.0;105.0,30.0;104.0,31.0|106.0,31.0;107.0,31.0;106.0,32.0",
                "districts": [{
                    "adcode": "510100", "name": "成都市", "level": "city",
                    "center": "104.06,30.67",
                }],
            }],
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        region = AmapDistrictClient("test-key", http=http).fetch_region("510000")

    assert region.code == "510000"
    assert region.polygons == [
        [[104.0, 30.0], [105.0, 30.0], [104.0, 31.0]],
        [[106.0, 31.0], [107.0, 31.0], [106.0, 32.0]],
    ]
    assert region.children[0].code == "510100"


def test_sync_requires_key_before_writing_regions(db_session) -> None:
    with pytest.raises(SystemExit, match="TRAVEL_AMAP_KEY is required"):
        run_sync(db_session, None, ["510000"])


def test_rejected_response_includes_safe_amap_reason() -> None:
    with httpx.Client(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json={"status": "0", "info": "CUQPS_HAS_EXCEEDED_THE_LIMIT", "infocode": "10003"})
    )) as http:
        client = AmapDistrictClient("test-key", http=http)
        with pytest.raises(AmapDistrictError, match="CUQPS_HAS_EXCEEDED_THE_LIMIT"):
            client.fetch_region("510000")


def test_client_throttles_follow_up_requests(monkeypatch) -> None:
    sleeps = []
    monkeypatch.setattr("app.map.amap.time.monotonic", lambda: 100.0)
    monkeypatch.setattr("app.map.amap.time.sleep", sleeps.append)
    payload = {"status": "1", "districts": [{
        "adcode": "510000", "name": "四川", "level": "province", "center": "102,30",
        "polyline": "100,29;104,29;102,32", "districts": [],
    }]}
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))) as http:
        client = AmapDistrictClient("test-key", http=http)
        client.fetch_region("510000")
        client.fetch_region("510000")
    assert sleeps == [0.6]


def test_fetch_adcode_resolves_a_destination_coordinate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v3/geocode/regeo"
        assert request.url.params["location"] == "104.06,30.67"
        return httpx.Response(200, json={
            "status": "1", "regeocode": {"addressComponent": {"adcode": "510107"}},
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        adcode = AmapDistrictClient("test-key", http=http).fetch_adcode(104.06, 30.67)

    assert adcode == "510107"


def test_fetch_region_retries_a_temporary_amap_rejection() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(200, json={"status": "0", "info": "CUQPS_HAS_EXCEEDED_THE_LIMIT"})
        return httpx.Response(200, json={"status": "1", "districts": [{
            "adcode": "510000", "name": "四川", "level": "province", "center": "102,30",
            "polyline": "100,29;104,29;102,32", "districts": [],
        }]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        client = AmapDistrictClient("test-key", http=http)
        client.retry_delay_seconds = 0
        assert client.fetch_region("510000").code == "510000"

    assert attempts == 2


def test_fetch_region_rejects_a_success_response_without_a_boundary() -> None:
    payload = {"status": "1", "districts": [{
        "adcode": "510000", "name": "四川", "level": "province", "center": "102,30",
        "polyline": "", "districts": [],
    }]}
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))) as http:
        client = AmapDistrictClient("test-key", http=http)
        client.retry_delay_seconds = 0
        with pytest.raises(AmapDistrictError, match="no usable boundary"):
            client.fetch_region("510000")


def test_city_assignment_uses_coordinate_adcode_when_destination_has_no_provider_code(db_session) -> None:
    db_session.add_all([
        AdministrativeRegion(code="510000", name="四川", level="province"),
        AdministrativeRegion(code="510100", name="成都", level="city", parent_code="510000"),
        Destination(
            code="chengdu", name="成都", latitude=30.67, longitude=104.06,
            region_code="510000", provider_adcode=None,
        ),
    ])
    db_session.commit()

    class Client:
        def fetch_adcode(self, longitude: float, latitude: float) -> str | None:
            assert (longitude, latitude) == (104.06, 30.67)
            return "510107"

    assert _assign_city_regions(db_session, Client()) == 0
    destination = db_session.scalar(select(Destination).where(Destination.code == "chengdu"))
    assert destination is not None
    assert destination.provider_adcode == "510107"
    assert destination.city_region_code == "510100"


def test_layer_sync_skips_boundaries_that_are_already_cached(db_session) -> None:
    db_session.add_all([
        AdministrativeRegion(code="510000", name="四川", level="province"),
        AdministrativeRegion(code="510100", name="成都", level="city", parent_code="510000"),
        RegionBoundary(
            region_code="510000", center_longitude=102, center_latitude=30,
            polygons=[[[100, 29], [104, 29], [102, 32]]], source="amap",
        ),
        RegionBoundary(
            region_code="510100", center_longitude=104, center_latitude=30,
            polygons=[[[103, 29], [105, 29], [104, 31]]], source="amap",
        ),
    ])
    db_session.commit()

    class Client:
        def fetch_region(self, _code: str) -> AmapRegion:
            raise AssertionError("cached regions must not be requested again")

    result = sync_region_layer(db_session, Client(), "510000")
    assert result == type(result)()


def test_layer_sync_replaces_an_empty_cached_city_boundary(db_session) -> None:
    db_session.add_all([
        AdministrativeRegion(code="510000", name="四川", level="province"),
        AdministrativeRegion(code="510100", name="成都", level="city", parent_code="510000"),
        RegionBoundary(
            region_code="510000", center_longitude=102, center_latitude=30,
            polygons=[[[100, 29], [104, 29], [102, 32]]], source="amap",
        ),
        RegionBoundary(
            region_code="510100", center_longitude=104, center_latitude=30,
            polygons=[], source="amap",
        ),
    ])
    db_session.commit()

    class Client:
        def fetch_region(self, code: str) -> AmapRegion:
            assert code == "510100"
            return AmapRegion("510100", "成都", "city", 104, 30, [
                [[103, 29], [105, 29], [104, 31]],
            ], [])

    result = sync_region_layer(db_session, Client(), "510000")
    assert result.boundaries_cached == 1
    assert db_session.get(RegionBoundary, "510100").polygons == [[[103, 29], [105, 29], [104, 31]]]


def test_layer_sync_keeps_successful_city_boundaries_when_one_city_is_rejected(db_session) -> None:
    db_session.add(AdministrativeRegion(code="510000", name="四川", level="province"))
    db_session.commit()

    class Client:
        def fetch_region(self, code: str) -> AmapRegion:
            if code == "510000":
                return AmapRegion("510000", "四川", "province", 102, 30, [[[100, 29], [104, 29], [102, 32]]], [
                    AmapRegionChild("510100", "成都", "city", 104, 30),
                    AmapRegionChild("510300", "自贡", "city", 104, 29),
                ])
            if code == "510100":
                return AmapRegion("510100", "成都", "city", 104, 30, [[[103, 29], [105, 29], [104, 31]]], [])
            raise AmapDistrictError("Amap rejected district request: CUQPS_HAS_EXCEEDED_THE_LIMIT")

    result = sync_region_layer(db_session, Client(), "510000")

    assert result.failures == 1
    assert db_session.get(RegionBoundary, "510000") is not None
    assert db_session.get(RegionBoundary, "510100") is not None
