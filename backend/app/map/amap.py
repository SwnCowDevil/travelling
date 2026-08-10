from dataclasses import dataclass
import time
from typing import Any

import httpx


class AmapDistrictError(RuntimeError):
    pass


class AmapDistrictConfigurationError(AmapDistrictError):
    pass


@dataclass(frozen=True)
class AmapRegionChild:
    code: str
    name: str
    level: str
    center_longitude: float | None
    center_latitude: float | None


@dataclass(frozen=True)
class AmapRegion:
    code: str
    name: str
    level: str
    center_longitude: float
    center_latitude: float
    polygons: list[list[list[float]]]
    children: list[AmapRegionChild]


def _center(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, str):
        return None
    try:
        longitude, latitude = value.split(",", 1)
        return float(longitude), float(latitude)
    except (TypeError, ValueError):
        return None


def parse_polygons(value: Any) -> list[list[list[float]]]:
    if not isinstance(value, str):
        return []
    polygons: list[list[list[float]]] = []
    for segment in value.split("|"):
        points: list[list[float]] = []
        for raw_point in segment.split(";"):
            point = _center(raw_point)
            if point is not None:
                points.append([point[0], point[1]])
        if len(points) >= 3:
            polygons.append(points)
    return polygons


class AmapDistrictClient:
    endpoint = "https://restapi.amap.com/v3/config/district"
    reverse_geocode_endpoint = "https://restapi.amap.com/v3/geocode/regeo"
    min_interval_seconds = 0.6
    max_attempts = 3
    retry_delay_seconds = 0.8

    def __init__(self, api_key: str | None, *, http: httpx.Client) -> None:
        self.api_key = api_key
        self.http = http
        self._last_request_at: float | None = None

    def _wait_for_request_slot(self) -> None:
        now = time.monotonic()
        if self._last_request_at is not None:
            remaining = self.min_interval_seconds - (now - self._last_request_at)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def _request_payload(self, endpoint: str, params: dict[str, object], subject: str) -> dict[str, Any]:
        last_error: AmapDistrictError | None = None
        for attempt in range(self.max_attempts):
            self._wait_for_request_slot()
            try:
                response = self.http.get(endpoint, params=params)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = AmapDistrictError(f"Amap {subject} request failed")
                last_error.__cause__ = exc
            else:
                if not isinstance(payload, dict):
                    last_error = AmapDistrictError(f"Amap returned an invalid {subject} response")
                elif payload.get("status") == "1":
                    return payload
                else:
                    info = str(payload.get("info") or payload.get("infocode") or "unknown")
                    last_error = AmapDistrictError(f"Amap rejected {subject} request: {info}")
            if attempt < self.max_attempts - 1:
                time.sleep(self.retry_delay_seconds * (2 ** attempt))
        assert last_error is not None
        raise last_error

    def fetch_region(self, adcode: str) -> AmapRegion:
        if not self.api_key:
            raise AmapDistrictConfigurationError("Amap district service is not configured")
        payload = self._request_payload(self.endpoint, {
            "key": self.api_key, "keywords": adcode,
            "subdistrict": 1, "extensions": "all",
        }, "district")
        districts = payload.get("districts")
        if not isinstance(districts, list) or not districts or not isinstance(districts[0], dict):
            raise AmapDistrictError("Amap returned no district")
        item = districts[0]
        center = _center(item.get("center"))
        code = str(item.get("adcode") or "").strip()
        name = str(item.get("name") or "").strip()
        level = str(item.get("level") or "").strip()
        if not code or not name or center is None:
            raise AmapDistrictError("Amap returned an invalid district")
        children: list[AmapRegionChild] = []
        raw_children = item.get("districts")
        if isinstance(raw_children, list):
            for child in raw_children:
                if not isinstance(child, dict):
                    continue
                child_code = str(child.get("adcode") or "").strip()
                child_name = str(child.get("name") or "").strip()
                child_level = str(child.get("level") or "").strip()
                child_center = _center(child.get("center"))
                if child_code and child_name and child_level:
                    children.append(AmapRegionChild(
                        code=child_code, name=child_name, level=child_level,
                        center_longitude=child_center[0] if child_center else None,
                        center_latitude=child_center[1] if child_center else None,
                    ))
        polygons = parse_polygons(item.get("polyline"))
        if not polygons:
            raise AmapDistrictError("Amap returned no usable boundary")
        return AmapRegion(
            code=code, name=name, level=level,
            center_longitude=center[0], center_latitude=center[1],
            polygons=polygons, children=children,
        )

    def fetch_adcode(self, longitude: float, latitude: float) -> str | None:
        if not self.api_key:
            raise AmapDistrictConfigurationError("Amap district service is not configured")
        payload = self._request_payload(self.reverse_geocode_endpoint, {
            "key": self.api_key, "location": f"{longitude},{latitude}", "extensions": "base",
        }, "reverse geocode")
        regeocode = payload.get("regeocode")
        component = regeocode.get("addressComponent") if isinstance(regeocode, dict) else None
        adcode = component.get("adcode") if isinstance(component, dict) else None
        value = str(adcode or "").strip()
        return value if len(value) == 6 and value.isdigit() else None
