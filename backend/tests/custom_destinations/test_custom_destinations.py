from app.custom_destinations.service import get_custom_destination, save_custom_destination
from app.users.models import User


def candidate() -> dict:
    return {"amap_poi_id": "B000A", "name": "杭州西湖", "address": "西湖区龙井路", "region_name": "浙江省杭州市", "latitude": 30.25, "longitude": 120.15}


def test_custom_destination_is_idempotent_per_user_poi(db_session) -> None:
    db_session.add_all([User(id=1, openid="custom-one"), User(id=2, openid="custom-two")])
    db_session.commit()
    first, created = save_custom_destination(db_session, 1, candidate())
    second, created_again = save_custom_destination(db_session, 1, candidate())

    assert created is True
    assert created_again is False
    assert first.id == second.id


def test_custom_destination_is_not_visible_to_other_users(db_session) -> None:
    db_session.add_all([User(id=1, openid="custom-one"), User(id=2, openid="custom-two")])
    db_session.commit()
    item, _ = save_custom_destination(db_session, 1, candidate())

    assert get_custom_destination(db_session, 2, item.id) is None
