import pytest

from app.destinations.models import AdministrativeRegion, Destination
from pydantic import ValidationError

from app.guides.schemas import (
    FoodRecommendation,
    GuideGenerationRequest,
    GuidePayload,
    ItineraryDay,
)
from app.guides.service import GuideService


def seed_destination(db_session) -> Destination:
    db_session.add(AdministrativeRegion(code="330000", name="浙江", level="province"))
    destination = Destination(
        code="hangzhou-west-lake",
        name="杭州西湖",
        summary="适合漫步的人文湖景",
        latitude=30.25,
        longitude=120.15,
        region_code="330000",
        categories=["人文", "景色"],
        suitable_months=[3, 4, 5, 9, 10, 11],
        season_tags=["旺季"],
        crowd_tags=["人多"],
        transport_modes=["高铁", "地铁"],
        climate={"summary": "春秋温和，雨水较多"},
        min_budget=600,
        max_budget=2200,
        min_days=2,
        max_days=3,
        quality_score=0.9,
        data_version="v1",
        coordinate_verified=True,
        coordinate_source="test",
    )
    db_session.add(destination)
    db_session.commit()
    return destination


def ai_payload() -> GuidePayload:
    return GuidePayload(
        transport=["乘高铁到杭州东站，再换乘地铁"],
        weather=["出发前查看逐日降雨概率"],
        packing=["雨伞", "舒适步行鞋"],
        cautions=["节假日提前预约"],
        highlights=["苏堤漫步", "参观浙江省博物馆"],
        foods=[
            FoodRecommendation(name="片儿川", description="笋片与雪菜汤面", area="湖滨", average_price="约25元/人"),
            FoodRecommendation(name="东坡肉", description="酥香软糯", area="河坊街", average_price="约60元/人"),
            FoodRecommendation(name="葱包桧", description="酥脆小吃", area="鼓楼", average_price="约10元/人"),
            FoodRecommendation(name="定胜糕", description="软糯米糕", area="南宋御街", average_price="约12元/人"),
        ],
        itinerary=[
            ItineraryDay(day=1, theme="西湖经典", morning="断桥", afternoon="苏堤", evening="湖滨", transport="步行和公交", caution="穿舒适鞋"),
            ItineraryDay(day=2, theme="人文老城", morning="灵隐寺", afternoon="河坊街", evening="南宋御街", transport="地铁和公交", caution="寺院保持安静"),
        ],
    )


def test_guide_payload_rejects_too_few_foods() -> None:
    value = ai_payload().model_dump()
    value["foods"] = value["foods"][:3]
    with pytest.raises(ValidationError):
        GuidePayload.model_validate(value)


def test_guide_payload_rejects_non_consecutive_days() -> None:
    value = ai_payload().model_dump()
    value["itinerary"][1]["day"] = 1
    with pytest.raises(ValidationError):
        GuidePayload.model_validate(value)


@pytest.mark.asyncio
async def test_same_cache_key_reuses_structured_guide(db_session) -> None:
    destination = seed_destination(db_session)
    calls = 0

    async def generator(**_kwargs) -> GuidePayload:
        nonlocal calls
        calls += 1
        return ai_payload()

    service = GuideService(generator=generator)
    request = GuideGenerationRequest(month=4, days=2, origin_name="上海")
    first = await service.generate(db_session, destination, request)
    second = await service.generate(db_session, destination, request)

    assert calls == 1
    assert second.cache_hit is True
    assert first.payload.model_dump() == second.payload.model_dump()
    assert set(GuidePayload.model_fields) == {
        "transport", "weather", "packing", "cautions", "highlights", "foods", "itinerary"
    }


@pytest.mark.asyncio
async def test_data_version_change_invalidates_cache(db_session) -> None:
    destination = seed_destination(db_session)
    calls = 0

    async def generator(**_kwargs) -> GuidePayload:
        nonlocal calls
        calls += 1
        return ai_payload()

    service = GuideService(generator=generator)
    request = GuideGenerationRequest(month=4, days=2, origin_name="上海")
    await service.generate(db_session, destination, request)
    destination.data_version = "v2"
    db_session.commit()
    await service.generate(db_session, destination, request)

    assert calls == 2


@pytest.mark.asyncio
async def test_ai_failure_returns_complete_basic_guide(db_session) -> None:
    destination = seed_destination(db_session)

    async def generator(**_kwargs) -> GuidePayload:
        raise TimeoutError("AI unavailable")

    result = await GuideService(generator=generator).generate(
        db_session,
        destination,
        GuideGenerationRequest(month=4, days=2, origin_name="上海"),
    )

    assert result.source == "rules"
    assert result.payload.transport
    assert result.payload.weather
    assert result.payload.packing
    assert result.payload.cautions
    assert result.payload.highlights
    assert len(result.payload.itinerary) == 2
