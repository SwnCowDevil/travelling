import pytest

from app.destinations.models import AdministrativeRegion, Destination
from app.guides.schemas import FoodRecommendation, GuidePayload, ItineraryDay
from app.favorites.service import get_favorite, save_favorite, update_favorite
from app.users.models import User


def destination(db_session) -> Destination:
    db_session.add_all([User(id=1, openid="favorite-owner"), User(id=2, openid="favorite-other")])
    db_session.add(AdministrativeRegion(code="330000", name="浙江", level="province"))
    item = Destination(
        code="hangzhou-west-lake", name="杭州西湖", summary="适合漫步的人文湖景",
        latitude=30.25, longitude=120.15, region_code="330000", categories=["景色"],
        suitable_months=[4], season_tags=[], crowd_tags=[], transport_modes=["地铁"],
        climate={}, min_budget=100, max_budget=200, min_days=2, max_days=2,
        quality_score=0.9, data_version="v1", coordinate_verified=True, coordinate_source="test",
    )
    db_session.add(item)
    db_session.commit()
    return item


def payload() -> GuidePayload:
    return GuidePayload(
        transport=["地铁"], weather=["晴"],
        packing=["身份证", "充电器", "充电宝", "雨伞", "防晒", "水杯", "常用药", "步行鞋"],
        cautions=["预约", "末班车", "天气", "安全", "官方公告"],
        highlights=["断桥", "苏堤", "曲院风荷", "北山街", "河坊街"],
        foods=[FoodRecommendation(name=name, description="当地风味", area="杭州", average_price="约30元") for name in ["片儿川", "东坡肉", "葱包桧", "定胜糕"]],
        itinerary=[ItineraryDay(day=1, theme="西湖", morning="断桥", afternoon="苏堤", evening="湖滨", transport="步行", caution="防晒")],
    )


def test_save_favorite_is_idempotent_per_user_and_destination(db_session) -> None:
    item = destination(db_session)
    first, created = save_favorite(db_session, 1, item, payload(), "fast")
    second, created_again = save_favorite(db_session, 1, item, payload(), "deep")

    assert created is True
    assert created_again is False
    assert first.id == second.id
    assert second.generation_mode == "fast"


def test_update_favorite_changes_only_the_owners_copy(db_session) -> None:
    item = destination(db_session)
    favorite, _ = save_favorite(db_session, 1, item, payload(), "fast")
    changed = payload()
    changed.highlights[0] = "编辑后的断桥玩法"

    assert update_favorite(db_session, 2, favorite.id, changed, "deep") is None
    saved = update_favorite(db_session, 1, favorite.id, changed, "deep")

    assert saved is not None
    assert saved.payload["highlights"][0] == "编辑后的断桥玩法"
    assert get_favorite(db_session, 2, favorite.id) is None
