from app.destinations.models import AdministrativeRegion, Destination
from app.map.models import RegionBoundary


def test_destination_can_keep_province_and_optional_city_boundary(db_session) -> None:
    province = AdministrativeRegion(code="510000", name="四川省", level="province")
    city = AdministrativeRegion(
        code="510100", name="成都市", level="city", parent_code="510000"
    )
    destination = Destination(
        code="chengdu-map", name="成都", summary="测试地点", latitude=104.06,
        longitude=30.67, region_code="510000", city_region_code="510100",
        categories=[], suitable_months=[], season_tags=[], crowd_tags=[],
        transport_modes=[], climate={}, quality_score=0.5, data_version="test",
        coordinate_verified=True, coordinate_source="test",
    )
    boundary = RegionBoundary(
        region_code="510100", center_longitude=104.06, center_latitude=30.67,
        polygons=[[[104.0, 30.6], [104.1, 30.6], [104.0, 30.7]]], source="amap",
    )
    db_session.add_all([province, city, destination, boundary])
    db_session.commit()

    assert db_session.get(Destination, destination.id).city_region_code == "510100"
    saved = db_session.get(RegionBoundary, "510100")
    assert saved is not None
    assert saved.polygons[0][0] == [104.0, 30.6]
