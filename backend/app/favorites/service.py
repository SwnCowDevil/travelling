from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.destinations.models import Destination
from app.favorites.models import FavoriteGuide
from app.guides.schemas import GuidePayload


def save_favorite(
    session: Session,
    user_id: int,
    destination: Destination,
    payload: GuidePayload,
    generation_mode: str,
    destination_type: str = "public",
    source: str = "unknown",
) -> tuple[FavoriteGuide, bool]:
    target_column = FavoriteGuide.custom_destination_id if destination_type == "custom" else FavoriteGuide.destination_id
    existing = session.scalar(select(FavoriteGuide).where(
        FavoriteGuide.user_id == user_id, target_column == destination.id
    ))
    if existing is not None:
        return existing, False
    favorite = FavoriteGuide(
        user_id=user_id,
        destination_id=destination.id if destination_type == "public" else None,
        custom_destination_id=destination.id if destination_type == "custom" else None,
        destination_type=destination_type,
        generation_mode=generation_mode,
        source=source,
        user_edited=False,
        payload=payload.model_dump(mode="json"),
        destination_snapshot={"name": destination.name, "summary": destination.summary, "emoji": "🏞️"},
    )
    session.add(favorite)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(select(FavoriteGuide).where(
            FavoriteGuide.user_id == user_id, target_column == destination.id
        ))
        if existing is not None:
            return existing, False
        raise
    session.refresh(favorite)
    return favorite, True


def get_favorite(session: Session, user_id: int, favorite_id: int) -> FavoriteGuide | None:
    return session.scalar(select(FavoriteGuide).where(
        FavoriteGuide.id == favorite_id, FavoriteGuide.user_id == user_id
    ))


def list_favorites(session: Session, user_id: int) -> list[FavoriteGuide]:
    return list(session.scalars(select(FavoriteGuide).where(
        FavoriteGuide.user_id == user_id
    ).order_by(FavoriteGuide.updated_at.desc(), FavoriteGuide.id.desc())).all())


def update_favorite(
    session: Session, user_id: int, favorite_id: int, payload: GuidePayload, generation_mode: str
) -> FavoriteGuide | None:
    favorite = get_favorite(session, user_id, favorite_id)
    if favorite is None:
        return None
    favorite.payload = payload.model_dump(mode="json")
    favorite.generation_mode = generation_mode
    favorite.user_edited = True
    session.commit()
    session.refresh(favorite)
    return favorite


def delete_favorite(session: Session, user_id: int, favorite_id: int) -> bool:
    favorite = get_favorite(session, user_id, favorite_id)
    if favorite is None:
        return False
    session.delete(favorite)
    session.commit()
    return True
