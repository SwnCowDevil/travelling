from dataclasses import dataclass
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

    def __init__(self, api_key: str | None, *, http: httpx.Client) -> None:
        self.api_key = api_key
        self.http = http

    def fetch_region(self, adcode: str) -> AmapRegion:
        if not self.api_key:
            raise AmapDistrictConfigurationError("Amap district service is not configured")
        try:
            response = self.http.get(self.endpoint, params={
                "key": self.api_key, "keywords": adcode,
                "subdistrict": 1, "extensions": "all",
            })
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AmapDistrictError("Amap district request failed") from exc
        districts = payload.get("districts") if isinstance(payload, dict) else None
        if payload.get("status") != "1" if isinstance(payload, dict) else True:
            raise AmapDistrictError("Amap rejected district request")
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
