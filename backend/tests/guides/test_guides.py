import pytest
from types import SimpleNamespace

from app.destinations.models import AdministrativeRegion, Destination
from pydantic import ValidationError

from app.guides.schemas import (
    FoodRecommendation,
    GuideGenerationRequest,
    GuidePayload,
    ItineraryDay,
)
from app.guides.service import GuideGenerationError, GuideService
from app.guides.router import _guide_prompt, build_guide_client, guide_timeout_seconds


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
        packing=["身份证", "雨伞", "舒适步行鞋", "充电器", "充电宝", "防晒霜", "水杯", "常用药"],
        cautions=["节假日提前预约", "确认末班车", "关注降雨", "保管证件", "以官方公告为准"],
        highlights=["苏堤漫步", "参观浙江省博物馆", "曲院风荷", "北山街夜景", "河坊街访古"],
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


def test_guide_payload_normalizes_daily_transport_string_list() -> None:
    value = ai_payload().model_dump()
    value["itinerary"][0]["transport"] = ["高铁", "景区公交"]

    payload = GuidePayload.model_validate(value)

    assert payload.itinerary[0].transport == "高铁；景区公交"


@pytest.mark.parametrize("mode", ["fast", "deep"])
def test_guide_prompt_requires_daily_itinerary_text_fields(mode: str) -> None:
    prompt = _guide_prompt(mode)

    assert (
        "theme、morning、afternoon、evening、transport、caution 都必须是字符串，不能是数组或对象"
        in prompt
    )


def test_personal_profile_timeout_is_extended_only_for_guides() -> None:
    assert guide_timeout_seconds(SimpleNamespace(timeout_seconds=20)) == 90


def test_official_deepseek_guide_clients_split_fast_and_deep() -> None:
    fast = build_guide_client(
        "https://api.deepseek.com", "sk-test", "deepseek-v4-flash", 45, "fast"
    )
    deep = build_guide_client(
        "https://api.deepseek.com", "sk-test", "deepseek-v4-pro", 90, "deep"
    )

    assert (fast.thinking_enabled, fast.max_tokens) == (False, 6000)
    assert (deep.thinking_enabled, deep.max_tokens) == (True, 12000)


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
async def test_fast_and_deep_guides_do_not_share_a_cache_entry(db_session) -> None:
    destination = seed_destination(db_session)
    calls = 0

    async def generator(**_kwargs) -> GuidePayload:
        nonlocal calls
        calls += 1
        return ai_payload()

    service = GuideService(generator=generator)
    fast = await service.generate(
        db_session,
        destination,
        GuideGenerationRequest(
            month=4, days=2, origin_name="上海", generation_mode="fast"
        ),
    )
    deep = await service.generate(
        db_session,
        destination,
        GuideGenerationRequest(
            month=4, days=2, origin_name="上海", generation_mode="deep"
        ),
    )

    assert calls == 2
    assert fast.cache_hit is False
    assert deep.cache_hit is False


@pytest.mark.asyncio
async def test_personal_guide_cache_scope_does_not_cross_users(db_session) -> None:
    destination = seed_destination(db_session)
    calls = 0

    async def generator(**_kwargs) -> GuidePayload:
        nonlocal calls
        calls += 1
        return ai_payload()

    request = GuideGenerationRequest(month=4, days=2, origin_name="上海", generation_mode="deep")
    await GuideService(generator=generator, cache_scope="user:1:model:pro").generate(db_session, destination, request)
    second = await GuideService(generator=generator, cache_scope="user:2:model:pro").generate(db_session, destination, request)

    assert calls == 2
    assert second.cache_hit is False


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
async def test_ai_failure_is_not_silently_replaced_with_rules(db_session) -> None:
    destination = seed_destination(db_session)

    async def generator(**_kwargs) -> GuidePayload:
        raise TimeoutError("AI unavailable")

    with pytest.raises(GuideGenerationError):
        await GuideService(generator=generator).generate(
            db_session,
            destination,
            GuideGenerationRequest(month=4, days=2, origin_name="上海"),
        )


@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache_and_replaces_it(db_session) -> None:
    destination = seed_destination(db_session)
    calls = 0

    async def generator(**_kwargs) -> GuidePayload:
        nonlocal calls
        calls += 1
        payload = ai_payload()
        payload.highlights[0] = f"第{calls}次生成的西湖玩法"
        return payload

    service = GuideService(generator=generator)
    request = GuideGenerationRequest(month=4, days=2, origin_name="上海")
    first = await service.generate(db_session, destination, request)
    refreshed = await service.generate(
        db_session,
        destination,
        GuideGenerationRequest(
            month=4, days=2, origin_name="上海", force_refresh=True
        ),
    )
    cached = await service.generate(db_session, destination, request)

    assert calls == 2
    assert first.payload.highlights[0] == "第1次生成的西湖玩法"
    assert refreshed.cache_hit is False
    assert refreshed.payload.highlights[0] == "第2次生成的西湖玩法"
    assert cached.cache_hit is True
    assert cached.payload.highlights[0] == "第2次生成的西湖玩法"


@pytest.mark.asyncio
async def test_force_refresh_ai_failure_preserves_cached_guide(db_session) -> None:
    destination = seed_destination(db_session)

    async def success(**_kwargs) -> GuidePayload:
        return ai_payload()

    request = GuideGenerationRequest(month=4, days=2, origin_name="上海")
    await GuideService(generator=success).generate(db_session, destination, request)

    async def failure(**_kwargs) -> GuidePayload:
        raise TimeoutError("AI unavailable")

    with pytest.raises(GuideGenerationError):
        await GuideService(generator=failure).generate(
            db_session,
            destination,
            GuideGenerationRequest(
                month=4, days=2, origin_name="上海", force_refresh=True
            ),
        )

    cached = await GuideService(generator=success).generate(
        db_session, destination, request
    )
    assert cached.cache_hit is True
    assert cached.payload.highlights == ai_payload().highlights


@pytest.mark.asyncio
async def test_force_refresh_without_ai_preserves_cached_guide(db_session) -> None:
    destination = seed_destination(db_session)

    async def success(**_kwargs) -> GuidePayload:
        return ai_payload()

    request = GuideGenerationRequest(month=4, days=2, origin_name="上海")
    await GuideService(generator=success).generate(db_session, destination, request)

    with pytest.raises(GuideGenerationError):
        await GuideService().generate(
            db_session,
            destination,
            GuideGenerationRequest(month=4, days=2, origin_name="上海", force_refresh=True),
        )

    cached = await GuideService(generator=success).generate(db_session, destination, request)
    assert cached.cache_hit is True
    assert cached.source == "ai"


@pytest.mark.asyncio
async def test_initial_load_without_ai_fails_instead_of_returning_generic_food(db_session) -> None:
    destination = seed_destination(db_session)
    with pytest.raises(GuideGenerationError):
        await GuideService().generate(
            db_session,
            destination,
            GuideGenerationRequest(month=4, days=2, origin_name="上海"),
        )


@pytest.mark.asyncio
async def test_ai_itinerary_must_match_requested_days(db_session) -> None:
    destination = seed_destination(db_session)

    async def incomplete(**_kwargs) -> GuidePayload:
        payload = ai_payload()
        payload.itinerary = payload.itinerary[:1]
        return payload

    with pytest.raises(GuideGenerationError):
        await GuideService(generator=incomplete).generate(
            db_session,
            destination,
            GuideGenerationRequest(month=4, days=2, origin_name="上海"),
        )
