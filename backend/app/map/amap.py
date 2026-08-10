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

    def fetch_region(self, adcode: str) -> AmapRegion:
        if not self.api_key:
            raise AmapDistrictConfigurationError("Amap district service is not configured")
        self._wait_for_request_slot()
        try:
            response = self.http.get(self.endpoint, params={
                "key": self.api_key, "keywords": adcode,
                "subdistrict": 1, "extensions": "all",
            })
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AmapDistrictError("Amap district request failed") from exc
        if not isinstance(payload, dict):
            raise AmapDistrictError("Amap returned an invalid district response")
        districts = payload.get("districts")
        if payload.get("status") != "1":
            info = str(payload.get("info") or payload.get("infocode") or "unknown")
            raise AmapDistrictError(f"Amap rejected district request: {info}")
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
        return AmapRegion(
            code=code, name=name, level=level,
            center_longitude=center[0], center_latitude=center[1],
            polygons=parse_polygons(item.get("polyline")), children=children,
        )

    def fetch_adcode(self, longitude: float, latitude: float) -> str | None:
        if not self.api_key:
            raise AmapDistrictConfigurationError("Amap district service is not configured")
        self._wait_for_request_slot()
        try:
            response = self.http.get(self.reverse_geocode_endpoint, params={
                "key": self.api_key, "location": f"{longitude},{latitude}", "extensions": "base",
            })
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AmapDistrictError("Amap reverse geocode request failed") from exc
        if not isinstance(payload, dict):
            raise AmapDistrictError("Amap returned an invalid reverse geocode response")
        if payload.get("status") != "1":
            info = str(payload.get("info") or payload.get("infocode") or "unknown")
            raise AmapDistrictError(f"Amap rejected reverse geocode request: {info}")
        regeocode = payload.get("regeocode")
        component = regeocode.get("addressComponent") if isinstance(regeocode, dict) else None
        adcode = component.get("adcode") if isinstance(component, dict) else None
        value = str(adcode or "").strip()
        return value if len(value) == 6 and value.isdigit() else None
