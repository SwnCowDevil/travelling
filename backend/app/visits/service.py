from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.footprints.models import DestinationStatus
from app.footprints.schemas import FootprintStatus
from app.footprints.service import set_destination_status
from app.visits.models import VisitRecord


class DuplicateVisitDate(ValueError):
    pass


class LastVisitRequiresStatusChange(ValueError):
    pass


@dataclass(frozen=True)
class VisitChange:
    record: VisitRecord
    visit_count: int
    destination_status: str


def count_visits(session: Session, user_id: int, destination_id: int) -> int:
    return int(session.scalar(select(func.count(VisitRecord.id)).where(
        VisitRecord.user_id == user_id,
        VisitRecord.destination_id == destination_id,
    )) or 0)


def create_visit(
    session: Session,
    user_id: int,
    destination_id: int,
    visited_on: date,
    *,
    note: str | None = None,
    idempotency_key: str | None = None,
    confirm_duplicate: bool = False,
) -> VisitChange:
    if idempotency_key:
        existing = session.scalar(select(VisitRecord).where(
            VisitRecord.user_id == user_id,
            VisitRecord.idempotency_key == idempotency_key,
        ))
        if existing:
            status = _status(session, user_id, existing.destination_id) or "visited"
            return VisitChange(existing, count_visits(session, user_id, existing.destination_id), status)
    duplicate = session.scalar(select(VisitRecord).where(
        VisitRecord.user_id == user_id,
        VisitRecord.destination_id == destination_id,
        VisitRecord.visited_on == visited_on,
    ))
    if duplicate and not confirm_duplicate:
        raise DuplicateVisitDate("visit already exists on this date")
    record = VisitRecord(
        user_id=user_id,
        destination_id=destination_id,
        visited_on=visited_on,
        note=note,
        idempotency_key=idempotency_key,
    )
    session.add(record)
    session.flush()
    total = count_visits(session, user_id, destination_id)
    current = _status(session, user_id, destination_id)
    if total == 1:
        change = set_destination_status(
            session, user_id, destination_id, FootprintStatus.VISITED, visit_count=1
        )
        current = change.status.status
    else:
        session.commit()
        session.refresh(record)
    return VisitChange(record, total, current or "visited")


def delete_visit(
    session: Session,
    user_id: int,
    visit_id: int,
    *,
    replacement_status: FootprintStatus | None = None,
) -> None:
    record = session.scalar(select(VisitRecord).where(
        VisitRecord.id == visit_id, VisitRecord.user_id == user_id
    ))
    if record is None:
        return
    total = count_visits(session, user_id, record.destination_id)
    current = _status(session, user_id, record.destination_id)
    if total == 1 and current == FootprintStatus.REVISIT.value:
        if replacement_status is None or replacement_status is FootprintStatus.REVISIT:
            raise LastVisitRequiresStatusChange("last revisit record needs replacement status")
    destination_id = record.destination_id
    session.delete(record)
    if total == 1 and replacement_status is not None:
        set_destination_status(
            session, user_id, destination_id, replacement_status, visit_count=0
        )
    else:
        session.commit()


def update_visit(
    session: Session,
    user_id: int,
    visit_id: int,
    *,
    visited_on: date | None = None,
    note: str | None = None,
    confirm_duplicate: bool = False,
) -> VisitRecord | None:
    record = session.scalar(select(VisitRecord).where(
        VisitRecord.id == visit_id, VisitRecord.user_id == user_id
    ))
    if record is None:
        return None
    if visited_on is not None and visited_on != record.visited_on:
        duplicate = session.scalar(select(VisitRecord).where(
            VisitRecord.user_id == user_id,
            VisitRecord.destination_id == record.destination_id,
            VisitRecord.visited_on == visited_on,
            VisitRecord.id != visit_id,
        ))
        if duplicate and not confirm_duplicate:
            raise DuplicateVisitDate("visit already exists on this date")
        record.visited_on = visited_on
    if note is not None:
        record.note = note
    session.commit()
    session.refresh(record)
    return record


def _status(session: Session, user_id: int, destination_id: int) -> str | None:
    return session.scalar(select(DestinationStatus.status).where(
        DestinationStatus.user_id == user_id,
        DestinationStatus.destination_id == destination_id,
    ))
