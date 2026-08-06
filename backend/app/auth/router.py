import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.schemas import AccessTokenResponse, WechatLoginRequest
from app.auth.service import create_access_token, get_or_create_user
from app.auth.wechat import WechatClient, WechatExchangeError
from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def get_wechat_client() -> WechatClient:
    return WechatClient(settings.wechat_app_id, settings.wechat_app_secret)


@router.post("/wechat", response_model=AccessTokenResponse)
async def login_with_wechat(
    body: WechatLoginRequest,
    session: Session = Depends(get_db),
    wechat: WechatClient = Depends(get_wechat_client),
) -> AccessTokenResponse:
    try:
        wechat_session = await wechat.exchange(body.code)
    except (WechatExchangeError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "WECHAT_LOGIN_FAILED", "message": "微信登录暂时不可用"},
        ) from exc
    user = get_or_create_user(session, wechat_session.openid)
    return AccessTokenResponse(
        access_token=create_access_token(user.id, settings.jwt_secret)
    )
