from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.auth.router import get_wechat_client
from app.auth.wechat import WechatSession
from app.db.session import get_db
from app.destinations.models import AdministrativeRegion, Destination
from app.main import create_app


class FakeWechatClient:
    async def exchange(self, _code: str) -> WechatSession:
        return WechatSession(openid="integration-user", session_key="private")


def test_login_recommend_visit_revisit_and_map_rollup(db_session) -> None:
    db_session.add_all([
        AdministrativeRegion(code="510000", name="四川", level="province"),
        AdministrativeRegion(code="513300", name="甘孜", level="city", parent_code="510000"),
        AdministrativeRegion(code="513337", name="稻城", level="county", parent_code="513300"),
    ])
    destination = Destination(
        code="integration-yading", name="稻城亚丁", summary="高原雪山与湖泊",
        latitude=28.47, longitude=100.28, region_code="513337", categories=["景色"],
        suitable_months=[9], season_tags=["旺季"], crowd_tags=["人多"],
        transport_modes=["飞机", "自驾"], climate={"summary": "早晚温差大"},
        min_budget=3000, max_budget=8000, min_days=5, max_days=8,
        quality_score=.95, data_version="v1", coordinate_verified=True,
        coordinate_source="test",
    )
    db_session.add(destination)
    db_session.commit()

    def override_db() -> Iterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_wechat_client] = lambda: FakeWechatClient()
    with TestClient(app) as client:
        login = client.post("/auth/wechat", json={"code": "wx-code"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        recommendation = client.post("/recommendations", headers=headers, json={
            "origin_latitude": 30.67,
            "origin_longitude": 104.06,
            "origin_name": "成都",
            "month": 9,
        })
        visit = client.post("/visit-records", headers=headers, json={
            "destination_id": destination.id,
            "visited_on": "2026-09-20",
            "idempotency_key": "trip-2026-yading",
        })
        revisit = client.put(
            f"/destination-statuses/{destination.id}",
            headers=headers,
            json={"status": "revisit"},
        )
        map_summary = client.get(
            "/map/summary", headers=headers, params={"status": "revisit"}
        )

    assert login.status_code == 200
    assert recommendation.status_code == 201
    assert recommendation.json()["items"][0]["code"] == "integration-yading"
    assert visit.json()["visit_count"] == 1
    assert revisit.json()["status"] == "revisit"
    assert map_summary.json()["items"][0]["region_code"] == "510000"
    assert map_summary.json()["items"][0]["visit_count"] == 1
