from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.custom_destinations.service import get_custom_destination
from app.db.session import get_db
from app.guides.router import get_guide_service
from app.guides.schemas import GuideGenerationRequest, GuidePayload
from app.guides.service import GuideGenerationError, GuideService

router = APIRouter(prefix="/custom-guides", tags=["custom-guides"])


@dataclass(frozen=True)
class CustomGuideContext:
    name: str
    summary: str


@router.post("/{destination_id}")
async def generate_custom_guide(
    destination_id: int,
    body: GuideGenerationRequest,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    service: GuideService = Depends(get_guide_service),
) -> dict:
    destination = get_custom_destination(session, user_id, destination_id)
    if destination is None:
        raise HTTPException(404, detail={"code": "CUSTOM_DESTINATION_NOT_FOUND"})
    if service.generator is None:
        raise HTTPException(502, detail={"code": "GUIDE_AI_GENERATION_FAILED", "message": "未配置可用的 AI"})
    try:
        payload = await service.generator(
            destination=CustomGuideContext(
                name=destination.name,
                summary=f"{destination.region_name} {destination.address}".strip(),
            ),
            request=body,
        )
        if len(payload.itinerary) != body.days:
            raise ValueError("itinerary length mismatch")
    except Exception as exc:
        raise HTTPException(502, detail={"code": "GUIDE_AI_GENERATION_FAILED", "message": "AI 攻略生成失败，请稍后重试"}) from exc
    return {"destination_id": destination.id, "source": "ai", "cache_hit": False, "data_version": "custom-v1", "payload": GuidePayload.model_validate(payload).model_dump(mode="json")}
