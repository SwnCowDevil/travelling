import pytest

from app.destinations.models import AdministrativeRegion, Destination
from app.footprints.models import DestinationStatus
from app.footprints.schemas import FootprintStatus
from app.footprints.service import InvalidFootprintTransition, set_destination_status
from app.users.models import User


def seed_entities(db_session) -> Destination:
    db_session.add(User(id=31, openid="footprint-user"))
    db_session.add(AdministrativeRegion(code="510000", name="四川", level="province"))
    destination = Destination(
        code="daochen-yading", name="稻城亚丁", summary="雪山与高原湖泊",
        latitude=28.47, longitude=100.28, region_code="510000",
        categories=["景色"], suitable_months=[5, 6, 9, 10], season_tags=["旺季"],
        crowd_tags=["人多"], transport_modes=["飞机", "自驾"], climate={},
        min_budget=3000, max_budget=8000, min_days=5, max_days=8,
        quality_score=0.9, data_version="v1", coordinate_verified=True,
        coordinate_source="test",
    )
    db_session.add(destination)
    db_session.commit()
    return destination


def test_destination_status_is_mutually_exclusive(db_session) -> None:
    destination = seed_entities(db_session)

    set_destination_status(db_session, 31, destination.id, FootprintStatus.WANT)
    set_destination_status(db_session, 31, destination.id, FootprintStatus.VISITED)

    statuses = db_session.query(DestinationStatus).filter_by(
        user_id=31, destination_id=destination.id
    ).all()
    assert len(statuses) == 1
    assert statuses[0].status == "visited"


def test_revisit_requires_at_least_one_visit(db_session) -> None:
    destination = seed_entities(db_session)

    with pytest.raises(InvalidFootprintTransition):
        set_destination_status(
            db_session, 31, destination.id, FootprintStatus.REVISIT, visit_count=0
        )


def test_avoid_preserves_history_and_returns_warning(db_session) -> None:
    destination = seed_entities(db_session)

    result = set_destination_status(
        db_session, 31, destination.id, FootprintStatus.AVOID, visit_count=2
    )

    assert result.status.status == "avoid"
    assert result.warning_code == "AVOID_WITH_VISIT_HISTORY"
