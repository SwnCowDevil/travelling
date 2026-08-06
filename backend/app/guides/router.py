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
from app.guides.service import GuideService

router = APIRouter(prefix="/guides", tags=["guides"])


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
                timeout_seconds=profile.timeout_seconds,
            )
            model = profile.model
        except Exception:
            client = None
    elif settings.ai_api_key:
        client = AIClient(settings.ai_base_url, settings.ai_api_key, settings.ai_model)
        model = settings.ai_model

    if client is None:
        return GuideService()

    async def generate(*, destination: Destination, request: GuideGenerationRequest) -> GuidePayload:
        payload = await client.complete_json(
            (
                "生成中国境内旅行攻略，严格返回 JSON 对象，字段为 transport、weather、"
                "packing、cautions、highlights、itinerary，且每个字段都是非空字符串数组。"
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
    days: int = Query(default=2, ge=1, le=30),
    origin_name: str = Query(min_length=1, max_length=100),
    _user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> GuideResponse:
    destination = _destination_or_404(session, destination_id)
    return await GuideService().generate(
        session,
        destination,
        GuideGenerationRequest(month=month, days=days, origin_name=origin_name),
    )


@router.post("/{destination_id}", response_model=GuideResponse)
async def generate_guide(
    destination_id: int,
    body: GuideGenerationRequest,
    _user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    service: GuideService = Depends(get_guide_service),
) -> GuideResponse:
    return await service.generate(
        session, _destination_or_404(session, destination_id), body
    )
