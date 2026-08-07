from dataclasses import dataclass
from typing import Any

import httpx


class AmapReverseError(RuntimeError):
    pass


class AmapConfigurationError(AmapReverseError):
    pass


@dataclass(frozen=True)
class ResolvedLocation:
    name: str
    region_name: str
    address: str
    latitude: float
    longitude: float
    source: str = "amap"


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _first_name(items: Any) -> str:
    if not isinstance(items, list):
        return ""
    for item in items:
        if isinstance(item, dict) and (name := _text(item.get("name"))):
            return name
    return ""


class AmapReverseClient:
    endpoint = "https://restapi.amap.com/v3/geocode/regeo"

    def __init__(self, api_key: str | None, *, http: httpx.AsyncClient) -> None:
        self.api_key = api_key
        self.http = http

    async def reverse(self, latitude: float, longitude: float) -> ResolvedLocation:
        if not self.api_key:
            raise AmapConfigurationError("Amap reverse geocoding is not configured")
        try:
            response = await self.http.get(
                self.endpoint,
                params={
                    "key": self.api_key,
                    "location": f"{longitude:.6f},{latitude:.6f}",
                    "extensions": "all",
                    "radius": "1000",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AmapReverseError("Amap reverse geocoding request failed") from exc

        if not isinstance(payload, dict) or payload.get("status") != "1":
            raise AmapReverseError("Amap rejected reverse geocoding request")
        regeocode = payload.get("regeocode")
        if not isinstance(regeocode, dict):
            raise AmapReverseError("Amap returned an invalid reverse geocoding payload")

        component = regeocode.get("addressComponent")
        component = component if isinstance(component, dict) else {}
        parts: list[str] = []
        for field in ("province", "city", "district"):
            value = _text(component.get(field))
            if value and value not in parts:
                parts.append(value)
        region_name = "".join(parts)
        address = _text(regeocode.get("formatted_address")) or region_name
        name = (
            _first_name(regeocode.get("pois"))
            or _first_name(regeocode.get("roads"))
            or address
            or region_name
        )
        if not name:
            raise AmapReverseError("Amap returned no usable location name")

        return ResolvedLocation(
            name=name,
            region_name=region_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
