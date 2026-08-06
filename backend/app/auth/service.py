from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.users.models import User


def get_or_create_user(session: Session, openid: str) -> User:
    user = session.scalar(select(User).where(User.openid == openid))
    if user is None:
        user = User(openid=openid)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def create_access_token(user_id: int, secret: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=1)},
        secret,
        algorithm="HS256",
    )
