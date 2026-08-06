from app.destinations.models import AdministrativeRegion, Destination
from app.users.models import User


def test_destination_links_to_region_by_stable_code(db_session) -> None:
    region = AdministrativeRegion(code="510000", name="四川省", level="province")
    place = Destination(
        code="sc-daocheng-yading",
        name="稻城亚丁",
        latitude=28.37,
        longitude=100.35,
        region_code="510000",
        categories=["山川", "景色"],
        suitable_months=[5, 6, 9, 10],
    )
    db_session.add_all([region, place])
    db_session.commit()

    assert place.region.name == "四川省"
    assert place.region_code == "510000"
    assert place.coordinate_verified is False


def test_user_openid_is_unique(db_session) -> None:
    first = User(openid="openid-1")
    db_session.add(first)
    db_session.commit()

    assert first.id is not None
    assert first.display_name == "微信用户"
