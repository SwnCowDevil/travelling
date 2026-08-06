from dataclasses import dataclass

import httpx


class AmapError(RuntimeError):
    pass


@dataclass(frozen=True)
class AmapPlace:
    longitude: float
    latitude: float
    provider_id: str
    province_name: str
    adcode: str | None = None


class AmapClient:
    endpoint = "https://restapi.amap.com/v3/place/text"

    def __init__(self, api_key: str, *, http: httpx.AsyncClient) -> None:
        self.api_key = api_key
        self.http = http

    async def search(
        self,
        name: str,
        region_code: str,
        province_name: str | None = None,
    ) -> AmapPlace:
        response = await self.http.get(
            self.endpoint,
            params={
                "key": self.api_key,
                "keywords": name,
                "city": region_code,
                "citylimit": "true",
                "offset": 5,
                "page": 1,
                "extensions": "base",
            },
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "1":
            raise AmapError(str(payload.get("info", "request failed")))
        pois = payload.get("pois", [])
        if not pois:
            raise AmapError(f"no POI found for {name}")
        poi = next(
            (candidate for candidate in pois if candidate.get("pname") == province_name),
            pois[0],
        )
        try:
            longitude, latitude = map(float, poi["location"].split(","))
            return AmapPlace(
                longitude=longitude,
                latitude=latitude,
                provider_id=str(poi["id"]),
                province_name=str(poi["pname"]),
                adcode=str(poi["adcode"]) if poi.get("adcode") else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AmapError(f"invalid POI response for {name}") from exc
