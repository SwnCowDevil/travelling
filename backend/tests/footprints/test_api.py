from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import AdministrativeRegion, Destination
from app.footprints.models import DestinationStatus, RegionStatus
from app.main import create_app
from app.users.models import User


def test_status_api_is_user_scoped_idempotent_and_clearable(db_session) -> None:
    db_session.add_all([
        User(id=51, openid="status-user-1"),
        User(id=52, openid="status-user-2"),
        AdministrativeRegion(code="320000", name="江苏", level="province"),
    ])
    destination = Destination(
        code="suzhou-gardens", name="苏州园林", summary="古典园林",
        latitude=31.3, longitude=120.6, region_code="320000", categories=["人文"],
        suitable_months=list(range(1, 13)), season_tags=[], crowd_tags=[],
        transport_modes=["高铁"], climate={}, min_budget=500, max_budget=2000,
        min_days=1, max_days=2, quality_score=.9, data_version="v1",
        coordinate_verified=True, coordinate_source="test",
    )
    db_session.add(destination)
    db_session.commit()
    active_user = {"id": 51}

    def override_db() -> Iterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: active_user["id"]
    with TestClient(app) as client:
        first = client.put(f"/destination-statuses/{destination.id}", json={"status": "want"})
        repeated = client.put(f"/destination-statuses/{destination.id}", json={"status": "want"})
        region = client.put("/region-statuses/320000", json={"status": "avoid"})
        active_user["id"] = 52
        other_delete = client.delete(f"/destination-statuses/{destination.id}")
        active_user["id"] = 51
        own_delete = client.delete(f"/destination-statuses/{destination.id}")
        region_delete = client.delete("/region-statuses/320000")

    assert first.status_code == repeated.status_code == 200
    assert region.status_code == 200
    assert other_delete.status_code == own_delete.status_code == 204
    assert db_session.query(DestinationStatus).count() == 0
    assert db_session.query(RegionStatus).count() == 0
