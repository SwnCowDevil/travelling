from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.crypto import TokenCipher
from app.ai.models import AIProfile
from app.ai.router import get_current_user_id
from app.core.config import settings
from app.db.session import get_db
from app.destinations.models import Destination
from app.guides.schemas import GuideGenerationRequest, GuidePayload, GuideResponse
from app.guides.service import GuideGenerationError, GuideService

router = APIRouter(prefix="/guides", tags=["guides"])


def guide_timeout_seconds(profile: AIProfile | None) -> int:
    return max(
        profile.timeout_seconds if profile is not None else 0,
        settings.ai_guide_timeout_seconds,
    )


def get_guide_service(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> GuideService:
    profile = session.scalar(select(AIProfile).where(AIProfile.user_id == user_id))
    client: AIClient | None = None
    model: str | None = None
    if profile is not None and settings.ai_encryption_key:
        try:
            token = TokenCipher.from_base64(settings.ai_encryption_key).decrypt(
                profile.encrypted_token
            )
            client = AIClient(
                profile.base_url,
                token,
                profile.model,
                timeout_seconds=guide_timeout_seconds(profile),
            )
            model = profile.model
        except Exception:
            client = None
    elif settings.ai_api_key:
        client = AIClient(
            settings.ai_base_url,
            settings.ai_api_key,
            settings.ai_model,
            timeout_seconds=guide_timeout_seconds(None),
        )
        model = settings.ai_model

    if client is None:
        return GuideService()

    async def generate(*, destination: Destination, request: GuideGenerationRequest) -> GuidePayload:
        payload = await client.complete_json(
            (
                "你是严谨的中国境内旅行规划师。只返回 JSON 对象，不要 Markdown。"
                "transport、weather、packing、cautions、highlights 都是非空字符串数组；"
                "packing 按证件/电子/衣物/天气/目的地特殊装备组织，共8至14项；"
                "cautions 为5至8条具体提醒，覆盖预约、交通、天气、安全和当地习俗；"
                "highlights 为5至8条真实景点或玩法，每条含名称与推荐理由；"
                "foods 为4至6个对象，每个严格包含 name、description、area、average_price，"
                "必须是真实当地美食，不可使用占位名称；"
                "itinerary 的天数必须与用户 days 完全一致，day 从1连续编号，每天严格包含"
                "day、theme、morning、afternoon、evening、transport、caution。早中晚写真实点位、"
                "建议时长、顺序和衔接，路线应可执行。不要编造精确票价、开放时间或临时政策，"
                "不确定的信息提醒用户出发前以官方信息为准。"
            ),
            request.model_dump_json()
            + f"\n目的地：{destination.name}\n简介：{destination.summary}",
        )
        return GuidePayload.model_validate(payload)

    return GuideService(generator=generate, model=model)


def _destination_or_404(session: Session, destination_id: int) -> Destination:
    destination = session.get(Destination, destination_id)
    if destination is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DESTINATION_NOT_FOUND", "message": "目的地不存在"},
        )
    return destination


@router.get("/{destination_id}", response_model=GuideResponse)
async def get_guide(
    destination_id: int,
    month: int = Query(ge=1, le=12),
    days: int = Query(default=2, ge=1, le=7),
    origin_name: str = Query(min_length=1, max_length=100),
    session: Session = Depends(get_db),
    service: GuideService = Depends(get_guide_service),
) -> GuideResponse:
    destination = _destination_or_404(session, destination_id)
    try:
        return await service.generate(
            session,
            destination,
            GuideGenerationRequest(month=month, days=days, origin_name=origin_name),
        )
    except GuideGenerationError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "GUIDE_AI_GENERATION_FAILED", "message": str(exc)},
        ) from exc


@router.post("/{destination_id}", response_model=GuideResponse)
async def generate_guide(
    destination_id: int,
    body: GuideGenerationRequest,
    _user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    service: GuideService = Depends(get_guide_service),
) -> GuideResponse:
    try:
        return await service.generate(
            session, _destination_or_404(session, destination_id), body
        )
    except GuideGenerationError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "GUIDE_AI_GENERATION_FAILED", "message": str(exc)},
        ) from exc
