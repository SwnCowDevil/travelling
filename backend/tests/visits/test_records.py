from datetime import date

import pytest

from app.destinations.models import AdministrativeRegion, Destination
from app.footprints.schemas import FootprintStatus
from app.footprints.service import set_destination_status
from app.users.models import User
from app.visits.service import (
    DuplicateVisitDate,
    LastVisitRequiresStatusChange,
    count_visits,
    create_visit,
    delete_visit,
)


def seed_destination_for_user(session, *, user_id: int) -> Destination:
    region_code = f"T{user_id}"
    session.add(User(id=user_id, openid=f"test-user-{user_id}"))
    session.add(AdministrativeRegion(code=region_code, name="测试区域", level="province"))
    destination = Destination(
        code=f"test-destination-{user_id}", name="测试目的地", summary="测试",
        latitude=30.0, longitude=120.0, region_code=region_code,
        categories=["景色"], suitable_months=list(range(1, 13)), season_tags=[],
        crowd_tags=[], transport_modes=["高铁"], climate={}, min_budget=100,
        max_budget=1000, min_days=1, max_days=2, quality_score=0.8,
        data_version="test", coordinate_verified=True, coordinate_source="test",
    )
    session.add(destination)
    session.commit()
    return destination


def test_first_visit_sets_visited_and_second_increments_count(db_session) -> None:
    destination = seed_destination_for_user(db_session, user_id=41)

    first = create_visit(db_session, 41, destination.id, date(2025, 4, 2))
    second = create_visit(db_session, 41, destination.id, date(2026, 4, 3))

    assert first.destination_status == "visited"
    assert second.visit_count == 2
    assert count_visits(db_session, 41, destination.id) == 2


def test_same_day_duplicate_requires_confirmation(db_session) -> None:
    destination = seed_destination_for_user(db_session, user_id=42)
    create_visit(db_session, 42, destination.id, date(2026, 5, 1))

    with pytest.raises(DuplicateVisitDate):
        create_visit(db_session, 42, destination.id, date(2026, 5, 1))

    confirmed = create_visit(
        db_session, 42, destination.id, date(2026, 5, 1), confirm_duplicate=True
    )
    assert confirmed.visit_count == 2


def test_deleting_last_revisit_requires_atomic_status_change(db_session) -> None:
    destination = seed_destination_for_user(db_session, user_id=43)
    created = create_visit(db_session, 43, destination.id, date(2026, 6, 1))
    set_destination_status(
        db_session, 43, destination.id, FootprintStatus.REVISIT, visit_count=1
    )

    with pytest.raises(LastVisitRequiresStatusChange):
        delete_visit(db_session, 43, created.record.id)

    delete_visit(
        db_session,
        43,
        created.record.id,
        replacement_status=FootprintStatus.WANT,
    )
    assert count_visits(db_session, 43, destination.id) == 0
