from sqlalchemy import select
from sqlalchemy.orm import Session

from app.custom_destinations.models import CustomDestination


def save_custom_destination(session: Session, user_id: int, candidate: dict) -> tuple[CustomDestination, bool]:
    existing = session.scalar(select(CustomDestination).where(CustomDestination.user_id == user_id, CustomDestination.amap_poi_id == candidate["amap_poi_id"]))
    if existing is not None:
        return existing, False
    item = CustomDestination(user_id=user_id, **candidate)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item, True


def get_custom_destination(session: Session, user_id: int, destination_id: int) -> CustomDestination | None:
    return session.scalar(select(CustomDestination).where(CustomDestination.user_id == user_id, CustomDestination.id == destination_id))
