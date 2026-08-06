import binascii
from collections.abc import Awaitable, Callable

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.client import AIClient
from app.ai.crypto import TokenCipher
from app.ai.models import AIProfile
from app.ai.profile import ProfileConnectionError, save_personal_profile
from app.ai.schemas import AIProfileResponse, AIProfileUpdate
from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/ai-profile", tags=["ai-profile"])
bearer = HTTPBearer()
ConnectionTest = Callable[..., Awaitable[None]]


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=["HS256"]
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN"}) from exc


def get_token_cipher() -> TokenCipher:
    if not settings.ai_encryption_key:
        raise HTTPException(
            status_code=503,
            detail={"code": "AI_ENCRYPTION_NOT_CONFIGURED"},
        )
    try:
        return TokenCipher.from_base64(settings.ai_encryption_key)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "AI_ENCRYPTION_KEY_INVALID"},
        ) from exc


def get_connection_test() -> ConnectionTest:
    async def test_connection(
        *, base_url: str, model: str, token: str, timeout_seconds: int
    ) -> None:
        await AIClient(
            base_url, token, model, timeout_seconds=timeout_seconds
        ).test_connection()

    return test_connection


def _system_profile() -> AIProfileResponse:
    return AIProfileResponse(
        mode="system",
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        protocol="chat_completions",
        timeout_seconds=20,
        group_note=None,
        masked_token=None,
        connection_status="configured" if settings.ai_api_key else "unconfigured",
    )


def _personal_profile(profile: AIProfile) -> AIProfileResponse:
    return AIProfileResponse(
        mode="personal",
        base_url=profile.base_url,
        model=profile.model,
        protocol=profile.protocol,
        timeout_seconds=profile.timeout_seconds,
        group_note=profile.group_note,
        masked_token=f"****{profile.token_last_four}",
        connection_status=profile.connection_status,
    )


@router.get("", response_model=AIProfileResponse)
def get_profile(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> AIProfileResponse:
    profile = session.scalar(select(AIProfile).where(AIProfile.user_id == user_id))
    return _personal_profile(profile) if profile else _system_profile()


@router.put("", response_model=AIProfileResponse)
async def put_profile(
    body: AIProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    cipher: TokenCipher = Depends(get_token_cipher),
    connection_test: ConnectionTest = Depends(get_connection_test),
) -> AIProfileResponse:
    try:
        profile = await save_personal_profile(
            session,
            user_id=user_id,
            base_url=str(body.base_url).rstrip("/"),
            model=body.model,
            token=body.token,
            protocol=body.protocol,
            timeout_seconds=body.timeout_seconds,
            group_note=body.group_note,
            cipher=cipher,
            connection_test=connection_test,
        )
    except ProfileConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "AI_CONNECTION_FAILED", "message": "AI 连接测试失败"},
        ) from exc
    return _personal_profile(profile)


@router.post("/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_profile_connection(
    body: AIProfileUpdate,
    _user_id: int = Depends(get_current_user_id),
    connection_test: ConnectionTest = Depends(get_connection_test),
) -> Response:
    try:
        await connection_test(
            base_url=str(body.base_url).rstrip("/"),
            model=body.model,
            token=body.token,
            timeout_seconds=body.timeout_seconds,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "AI_CONNECTION_FAILED", "message": "AI 连接测试失败"},
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> Response:
    profile = session.scalar(select(AIProfile).where(AIProfile.user_id == user_id))
    if profile:
        session.delete(profile)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
