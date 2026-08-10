import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.destinations.models import Destination
from app.guides.models import GuideCache
from app.guides.schemas import (
    GuideGenerationRequest,
    GuidePayload,
    GuideResponse,
)

GuideGenerator = Callable[..., Awaitable[GuidePayload]]
GUIDE_CONTENT_VERSION = "rich-v2"


class GuideGenerationError(RuntimeError):
    """Raised when an explicit AI regeneration cannot be completed."""


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
        conditions = request.model_dump(mode="json", exclude={"force_refresh"})
        cache_key = self._cache_key(destination, conditions)
        cached = session.scalar(select(GuideCache).where(GuideCache.cache_key == cache_key))
        now = datetime.now(timezone.utc)
        if (
            not request.force_refresh
            and cached is not None
            and _as_utc(cached.expires_at) > now
        ):
            try:
                return self._response(destination, cached, cache_hit=True)
            except ValueError:
                # Ignore caches created with an older payload schema.
                pass

        if self.generator is None:
            raise GuideGenerationError("未配置可用的 AI，请先在我的页面完成 AI 设置")
        try:
            payload = await self.generator(destination=destination, request=request)
            if len(payload.itinerary) != request.days:
                raise ValueError("AI itinerary length does not match requested days")
        except Exception as exc:
            raise GuideGenerationError("AI 攻略生成失败，请稍后重试") from exc

        cache = cached or GuideCache(destination_id=destination.id, cache_key=cache_key)
        cache.conditions = conditions
        cache.payload = payload.model_dump(mode="json")
        cache.source = "ai"
        cache.model = self.model
        cache.data_version = destination.data_version
        cache.expires_at = (now + timedelta(days=30)).replace(tzinfo=None)
        if cached is None:
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
                "guide_content_version": GUIDE_CONTENT_VERSION,
                "conditions": conditions,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

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
