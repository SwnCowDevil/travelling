from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.client import AIClient
from app.ai.crypto import TokenCipher
from app.ai.models import AIProfile
from app.ai.router import get_current_user_id
from app.core.config import settings
from app.db.session import get_db
from app.recommendations.models import RecommendationSession
from app.recommendations.schemas import (
    RecommendationCreate,
    RecommendationHistoryItem,
    RecommendationHistoryResponse,
    RecommendationResponse,
)
from app.recommendations.service import (
    Reranker,
    create_recommendation,
    next_recommendation_batch,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_reranker(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> Reranker | None:
    profile = session.scalar(select(AIProfile).where(AIProfile.user_id == user_id))
    if profile is not None:
        if not settings.ai_encryption_key:
            return None
        try:
            token = TokenCipher.from_base64(settings.ai_encryption_key).decrypt(
                profile.encrypted_token
            )
        except Exception:
            return None
        client = AIClient(
            profile.base_url,
            token,
            profile.model,
            timeout_seconds=profile.timeout_seconds,
        )
        return client.rerank
    if not settings.ai_api_key:
        return None
    return AIClient(settings.ai_base_url, settings.ai_api_key, settings.ai_model).rerank


@router.post("", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def recommend(
    body: RecommendationCreate,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    reranker: Reranker | None = Depends(get_reranker),
) -> RecommendationResponse:
    return await create_recommendation(
        session, user_id=user_id, body=body, reranker=reranker
    )


@router.post("/{session_id}/next", response_model=RecommendationResponse)
async def next_batch(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    reranker: Reranker | None = Depends(get_reranker),
) -> RecommendationResponse:
    record = session.scalar(
        select(RecommendationSession).where(
            RecommendationSession.id == session_id,
            RecommendationSession.user_id == user_id,
        )
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "RECOMMENDATION_SESSION_NOT_FOUND", "message": "推荐记录不存在"},
        )
    return await next_recommendation_batch(session, record=record, reranker=reranker)


@router.get("/history", response_model=RecommendationHistoryResponse)
def history(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> RecommendationHistoryResponse:
    records = session.scalars(
        select(RecommendationSession)
        .where(RecommendationSession.user_id == user_id)
        .order_by(RecommendationSession.created_at.desc(), RecommendationSession.id.desc())
    ).all()
    return RecommendationHistoryResponse(items=[
        RecommendationHistoryItem(
            session_id=record.id,
            origin_name=str(record.query["origin_name"]),
            month=int(record.query["month"]),
            shown_count=len(record.shown_codes),
            source=record.source,
            created_at=record.created_at,
        )
        for record in records
    ])
