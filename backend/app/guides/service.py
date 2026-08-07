import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.destinations.models import Destination
from app.guides.models import GuideCache
from app.guides.schemas import (
    FoodRecommendation,
    GuideGenerationRequest,
    GuidePayload,
    GuideResponse,
    ItineraryDay,
)

GuideGenerator = Callable[..., Awaitable[GuidePayload]]


class GuideService:
    def __init__(self, generator: GuideGenerator | None = None, model: str | None = None) -> None:
        self.generator = generator
        self.model = model

    async def generate(
        self,
        session: Session,
        destination: Destination,
        request: GuideGenerationRequest,
    ) -> GuideResponse:
        conditions = request.model_dump(mode="json")
        cache_key = self._cache_key(destination, conditions)
        cached = session.scalar(select(GuideCache).where(GuideCache.cache_key == cache_key))
        now = datetime.now(timezone.utc)
        if cached is not None and _as_utc(cached.expires_at) > now:
            return self._response(destination, cached, cache_hit=True)

        source = "rules"
        payload = self._basic_guide(destination, request)
        if self.generator is not None:
            try:
                payload = await self.generator(destination=destination, request=request)
                source = "ai"
            except Exception:
                pass

        cache = GuideCache(
            destination_id=destination.id,
            cache_key=cache_key,
            conditions=conditions,
            payload=payload.model_dump(mode="json"),
            source=source,
            model=self.model if source == "ai" else None,
            data_version=destination.data_version,
            expires_at=(now + timedelta(days=30)).replace(tzinfo=None),
        )
        session.add(cache)
        session.commit()
        session.refresh(cache)
        return self._response(destination, cache, cache_hit=False)

    @staticmethod
    def _cache_key(destination: Destination, conditions: dict) -> str:
        raw = json.dumps(
            {
                "destination_id": destination.id,
                "data_version": destination.data_version,
                "conditions": conditions,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _basic_guide(
        destination: Destination, request: GuideGenerationRequest
    ) -> GuidePayload:
        transports = "、".join(destination.transport_modes) or "公共交通"
        climate = destination.climate.get("summary", "出发前查看最新天气预报")
        packing = ["身份证件", "充电设备", "舒适步行鞋"]
        if "雨" in climate:
            packing.append("雨具")
        highlights = [destination.summary, *destination.categories[:2]]
        highlights = [value for value in highlights if value] or [destination.name]
        return GuidePayload(
            transport=[f"从{request.origin_name}出发，优先考虑{transports}"],
            weather=[climate, "临行前再次确认逐日天气与预警"],
            packing=packing,
            cautions=["提前确认开放时间和预约要求", "旺季预留排队与交通时间"],
            highlights=highlights,
            foods=[
                FoodRecommendation(
                    name=f"{destination.name}特色风味{index}",
                    description=f"结合当地饮食特色的第{index}项尝鲜选择",
                    area=f"{destination.name}主要游览区",
                    average_price="价格以门店现场为准",
                )
                for index in range(1, 5)
            ],
            itinerary=[
                ItineraryDay(
                    day=day,
                    theme=f"{destination.name}第{day}天探索",
                    morning=f"上午游览{highlights[(day - 1) % len(highlights)]}",
                    afternoon=f"下午体验{highlights[day % len(highlights)]}",
                    evening=f"晚上品尝{destination.name}当地风味并休息",
                    transport=f"当天优先使用{transports}",
                    caution="合理安排节奏，提前确认开放时间",
                )
                for day in range(1, request.days + 1)
            ],
        )

    @staticmethod
    def _response(
        destination: Destination, cache: GuideCache, *, cache_hit: bool
    ) -> GuideResponse:
        return GuideResponse(
            destination_id=destination.id,
            destination_code=destination.code,
            source=cache.source,
            cache_hit=cache_hit,
            data_version=cache.data_version,
            payload=GuidePayload.model_validate(cache.payload),
        )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
