from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.footprints.models import DestinationStatus, RegionStatus
from app.footprints.schemas import FootprintStatus


class InvalidFootprintTransition(ValueError):
    pass


@dataclass(frozen=True)
class StatusChange:
    status: DestinationStatus | RegionStatus
    warning_code: str | None = None


def set_destination_status(
    session: Session,
    user_id: int,
    destination_id: int,
    status: FootprintStatus,
    *,
    visit_count: int = 0,
) -> StatusChange:
    if status is FootprintStatus.REVISIT and visit_count < 1:
        raise InvalidFootprintTransition("revisit requires at least one visit")
    record = session.scalar(select(DestinationStatus).where(
        DestinationStatus.user_id == user_id,
        DestinationStatus.destination_id == destination_id,
    ))
    if record is None:
        record = DestinationStatus(user_id=user_id, destination_id=destination_id)
        session.add(record)
    record.status = status.value
    session.commit()
    session.refresh(record)
    warning = (
        "AVOID_WITH_VISIT_HISTORY"
        if status is FootprintStatus.AVOID and visit_count > 0
        else None
    )
    return StatusChange(status=record, warning_code=warning)


def set_region_status(
    session: Session,
    user_id: int,
    region_code: str,
    status: FootprintStatus,
) -> StatusChange:
    record = session.scalar(select(RegionStatus).where(
        RegionStatus.user_id == user_id,
        RegionStatus.region_code == region_code,
    ))
    if record is None:
        record = RegionStatus(user_id=user_id, region_code=region_code)
        session.add(record)
    record.status = status.value
    session.commit()
    session.refresh(record)
    return StatusChange(status=record)


def clear_status(session: Session, record: DestinationStatus | RegionStatus | None) -> None:
    if record is not None:
        session.delete(record)
        session.commit()
