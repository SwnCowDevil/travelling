from datetime import date

from app.destinations.models import AdministrativeRegion, Destination
from app.footprints.schemas import FootprintStatus
from app.footprints.service import set_destination_status, set_region_status
from app.map.models import RegionBoundary
from app.map.service import build_map_summary, simplify_map_polygons
from app.users.models import User
from app.visits.service import create_visit


def test_destination_rolls_up_ancestors_without_overwriting_direct_status(db_session) -> None:
    db_session.add(User(id=61, openid="map-user"))
    db_session.add_all([
        AdministrativeRegion(code="510000", name="四川", level="province"),
        AdministrativeRegion(code="513300", name="甘孜", level="city", parent_code="510000"),
        AdministrativeRegion(code="513337", name="稻城", level="county", parent_code="513300"),
    ])
    destination = Destination(
        code="daochen-yading-map", name="稻城亚丁", summary="高原景区",
        latitude=28.47, longitude=100.28, region_code="513337", categories=["景色"],
        suitable_months=[5, 6, 9, 10], season_tags=[], crowd_tags=[],
        transport_modes=["自驾"], climate={}, min_budget=3000, max_budget=8000,
        min_days=5, max_days=8, quality_score=.9, data_version="v1",
        coordinate_verified=True, coordinate_source="test",
    )
    db_session.add(destination)
    db_session.commit()
    create_visit(db_session, 61, destination.id, date(2026, 5, 1))
    set_destination_status(
        db_session, 61, destination.id, FootprintStatus.REVISIT, visit_count=1
    )
    set_region_status(db_session, 61, "510000", FootprintStatus.AVOID)

    root = build_map_summary(db_session, 61, parent_code=None, status="revisit")
    city = build_map_summary(db_session, 61, parent_code="510000", status="revisit")

    assert [item.region_code for item in root] == ["510000"]
    assert root[0].direct_status == "avoid"
    assert root[0].status_counts["revisit"] == 1
    assert root[0].visit_count == 1
    assert [item.region_code for item in city] == ["513300"]
    assert city[0].direct_status is None


def test_summary_returns_lightweight_status_and_rolls_city_status_up_to_province(db_session) -> None:
    db_session.add(User(id=62, openid="map-city-user"))
    db_session.add_all([
        AdministrativeRegion(code="330000", name="浙江", level="province"),
        AdministrativeRegion(code="330100", name="杭州", level="city", parent_code="330000"),
        RegionBoundary(region_code="330000", center_longitude=120.1, center_latitude=29.1, polygons=[[[119.0, 28.0], [121.0, 28.0], [120.0, 30.0]]]),
        RegionBoundary(region_code="330100", center_longitude=120.2, center_latitude=30.2, polygons=[[[120.0, 30.0], [120.4, 30.0], [120.2, 30.4]]]),
    ])
    destination = Destination(
        code="west-lake-map", name="西湖", summary="湖景", latitude=30.2, longitude=120.1,
        region_code="330000", city_region_code="330100", categories=[], suitable_months=[],
        season_tags=[], crowd_tags=[], transport_modes=[], climate={}, quality_score=.8,
        data_version="v1", coordinate_verified=True, coordinate_source="test",
    )
    db_session.add(destination)
    db_session.commit()
    set_destination_status(db_session, 62, destination.id, FootprintStatus.WANT)

    province = build_map_summary(db_session, 62, parent_code=None)
    city = build_map_summary(db_session, 62, parent_code="330000")

    assert province[0].map_status == "want"
    assert province[0].center == [120.1, 29.1]
    assert province[0].polygons == []
    assert city[0].region_code == "330100"
    assert city[0].map_status == "want"
    assert city[0].polygons == []


def test_simplify_map_polygons_limits_geometry_without_mutating_source() -> None:
    long_outline = [[float(index), float(index % 11)] for index in range(900)]
    islands = [
        [[120.0 + index, 20.0], [120.4 + index, 20.0], [120.2 + index, 20.4]]
        for index in range(16)
    ]
    item = simplify_map_polygons([long_outline, *islands])

    assert len(item) <= 4
    assert sum(len(path) for path in item) <= 80
    assert item[0][0] == long_outline[0]
    assert item[0][-1] == long_outline[-1]
