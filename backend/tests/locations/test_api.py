from fastapi.testclient import TestClient

from app.ai.router import get_current_user_id
from app.locations.amap import AmapConfigurationError, AmapReverseError, ResolvedLocation
from app.locations.router import get_reverse_client
from app.main import create_app


class FakeReverseClient:
    async def reverse(self, latitude: float, longitude: float) -> ResolvedLocation:
        return ResolvedLocation(
            name="天安门",
            region_name="北京市东城区",
            address="北京市东城区东长安街",
            latitude=latitude,
            longitude=longitude,
        )


class FailingReverseClient:
    def __init__(self, error: AmapReverseError):
        self.error = error

    async def reverse(self, latitude: float, longitude: float) -> ResolvedLocation:
        raise self.error


def test_reverse_geocode_requires_authentication():
    response = TestClient(create_app()).get(
        "/locations/reverse-geocode?latitude=39.9&longitude=116.4"
    )
    assert response.status_code == 403


def test_reverse_geocode_returns_normalized_location():
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: 1
    app.dependency_overrides[get_reverse_client] = lambda: FakeReverseClient()
    response = TestClient(app).get(
        "/locations/reverse-geocode?latitude=39.9&longitude=116.4"
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "天安门",
        "region_name": "北京市东城区",
        "address": "北京市东城区东长安街",
        "latitude": 39.9,
        "longitude": 116.4,
        "source": "amap",
    }


def test_reverse_geocode_validates_coordinate_ranges():
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: 1
    app.dependency_overrides[get_reverse_client] = lambda: FakeReverseClient()
    client = TestClient(app)

    assert client.get("/locations/reverse-geocode?latitude=91&longitude=116").status_code == 422
    assert client.get("/locations/reverse-geocode?latitude=39&longitude=181").status_code == 422


def test_reverse_geocode_maps_missing_configuration_to_stable_error():
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: 1
    app.dependency_overrides[get_reverse_client] = lambda: FailingReverseClient(
        AmapConfigurationError("not configured")
    )
    response = TestClient(app).get(
        "/locations/reverse-geocode?latitude=39.9&longitude=116.4"
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "LOCATION_SERVICE_UNAVAILABLE"


def test_reverse_geocode_maps_upstream_failure_to_stable_error():
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: 1
    app.dependency_overrides[get_reverse_client] = lambda: FailingReverseClient(
        AmapReverseError("request failed")
    )
    response = TestClient(app).get(
        "/locations/reverse-geocode?latitude=39.9&longitude=116.4"
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "LOCATION_LOOKUP_FAILED"
