import httpx
import pytest

from app.map.amap import AmapDistrictClient
from scripts.sync_map_regions import run_sync


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
