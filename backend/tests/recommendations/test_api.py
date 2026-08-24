from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import AdministrativeRegion, Destination
from app.main import create_app
from app.footprints.models import DestinationStatus
from app.recommendations.router import get_reranker
from app.recommendations.schemas import RecommendationCreate
from app.users.models import User


def seed_destinations(db_session) -> None:
    db_session.add(User(id=21, openid="recommendation-user"))
    db_session.add(AdministrativeRegion(code="310000", name="上海", level="province"))
    coordinates = [
        ("near-1", 31.20, 121.45),
        ("near-2", 31.25, 121.48),
        ("near-3", 31.30, 121.50),
        ("near-4", 31.35, 121.52),
        ("near-5", 31.40, 121.55),
        ("near-6", 31.45, 121.58),
        ("near-7", 31.50, 121.60),
        ("far-away", 39.90, 116.40),
    ]
    for index, (code, latitude, longitude) in enumerate(coordinates, start=1):
        db_session.add(Destination(
            code=code,
            name=f"目的地 {index}",
            summary="测试目的地",
            latitude=latitude,
            longitude=longitude,
            region_code="310000",
            categories=["景色"],
            suitable_months=[4],
            season_tags=["平季"],
            crowd_tags=["人少"],
            transport_modes=["自驾"],
            climate={},
            min_budget=500,
            max_budget=1500,
            min_days=1,
            max_days=2,
            quality_score=1 - index * 0.05,
            data_version="test-v1",
            coordinate_verified=True,
            coordinate_source="test",
        ))
    db_session.commit()


def test_recommendation_falls_back_rotates_and_preserves_hard_filters(db_session, caplog) -> None:
    seed_destinations(db_session)
    avoided = db_session.query(Destination).filter_by(code="near-1").one()
    db_session.add(DestinationStatus(user_id=21, destination_id=avoided.id, status="avoid"))
    db_session.commit()

    async def timed_out_reranker(_request):
        raise TimeoutError("AI timed out")

    def override_db() -> Iterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: 21
    app.dependency_overrides[get_reranker] = lambda: timed_out_reranker

    request = {
        "origin_latitude": 31.2304,
        "origin_longitude": 121.4737,
        "origin_name": "上海",
        "month": 4,
        "max_distance_km": 100,
    }
    with TestClient(app) as client:
        first = client.post("/recommendations", json=request)
        second = client.post(f"/recommendations/{first.json()['session_id']}/next")
        history = client.get("/recommendations/history")

    assert first.status_code == 201
    assert first.json()["source"] == "rules"
    assert len(first.json()["items"]) == 3
    assert len(second.json()["items"]) == 3
    first_codes = {item["code"] for item in first.json()["items"]}
    second_codes = {item["code"] for item in second.json()["items"]}
    assert first_codes.isdisjoint(second_codes)
    assert "far-away" not in first_codes | second_codes
    assert "near-1" not in first_codes | second_codes
    assert history.json()["items"][0]["session_id"] == first.json()["session_id"]
    assert "AI recommendation rerank failed" in caplog.text


def test_candidate_shortage_never_relaxes_distance_filter(db_session) -> None:
    seed_destinations(db_session)

    def override_db() -> Iterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: 21
    app.dependency_overrides[get_reranker] = lambda: None

    with TestClient(app) as client:
        response = client.post("/recommendations", json={
            "origin_latitude": 31.2304,
            "origin_longitude": 121.4737,
            "origin_name": "上海",
            "month": 4,
            "max_distance_km": 5,
        })

    assert response.status_code == 201
    assert 0 < len(response.json()["items"]) < 3
    assert all(item["distance_km"] <= 5 for item in response.json()["items"])


def test_recommendation_respects_a_distance_range(db_session) -> None:
    seed_destinations(db_session)

    def override_db() -> Iterator:
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: 21
    app.dependency_overrides[get_reranker] = lambda: None

    with TestClient(app) as client:
        response = client.post("/recommendations", json={
            "origin_latitude": 31.2304,
            "origin_longitude": 121.4737,
            "origin_name": "上海",
            "month": 4,
            "min_distance_km": 20,
            "max_distance_km": 30,
        })

    assert response.status_code == 201
    assert response.json()["items"]
    assert all(20 <= item["distance_km"] < 30 for item in response.json()["items"])


@pytest.mark.parametrize("payload", [
    {"min_distance_km": -1},
    {"min_distance_km": 200, "max_distance_km": 200},
    {"min_distance_km": 300, "max_distance_km": 200},
])
def test_recommendation_rejects_invalid_distance_ranges(payload: dict) -> None:
    with pytest.raises(ValidationError):
        RecommendationCreate(
            origin_latitude=31.2304,
            origin_longitude=121.4737,
            origin_name="上海",
            month=4,
            **payload,
        )
