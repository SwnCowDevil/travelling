from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.crypto import TokenCipher
from app.ai.models import AIProfile


class ProfileConnectionError(RuntimeError):
    pass


async def save_personal_profile(
    session: Session,
    *,
    user_id: int,
    base_url: str,
    model: str,
    token: str,
    protocol: str,
    timeout_seconds: int,
    group_note: str | None,
    cipher: TokenCipher,
    connection_test: Callable[..., Awaitable[None]],
) -> AIProfile:
    try:
        await connection_test(
            base_url=base_url,
            model=model,
            token=token,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        raise ProfileConnectionError("AI connection test failed") from exc

    profile = session.scalar(select(AIProfile).where(AIProfile.user_id == user_id))
    if profile is None:
        profile = AIProfile(user_id=user_id)
        session.add(profile)
    profile.base_url = base_url
    profile.model = model
    profile.protocol = protocol
    profile.timeout_seconds = timeout_seconds
    profile.group_note = group_note
    profile.encrypted_token = cipher.encrypt(token)
    profile.token_last_four = token[-4:]
    profile.connection_status = "ok"
    session.commit()
    session.refresh(profile)
    return profile
