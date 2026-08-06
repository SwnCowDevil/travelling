import asyncio
import json
from pathlib import Path
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.destinations.amap import AmapError, AmapPlace


SEARCH_ALIASES = {
    "厦门鼓浪屿": "鼓浪屿风景名胜区",
    "潮州古城": "潮州古城牌坊街",
    "重庆洪崖洞": "洪崖洞民俗风貌区",
    "赛里木湖": "赛里木湖国家级风景名胜区",
    "独库公路": "独库公路博物馆",
}


class PlaceSearcher(Protocol):
    async def search(
        self, name: str, region_code: str, province_name: str | None = None
    ) -> AmapPlace: ...


async def calibrate_payload(
    payload: dict[str, Any],
    client: PlaceSearcher,
    *,
    delay_seconds: float = 0,
) -> dict[str, Any]:
    verified = 0
    unresolved: list[str] = []
    region_names = {item["code"]: item["name"] for item in payload.get("regions", [])}
    for item in payload["destinations"]:
        if item.get("coordinate_verified"):
            verified += 1
            continue
        item["coordinate_verified"] = False
        item["coordinate_source"] = "approximate"
        if item["region_code"] == "710000":
            unresolved.append(item["name"])
            continue
        place = None
        search_terms = [item["name"]]
        if alias := SEARCH_ALIASES.get(item["name"]):
            search_terms.append(alias)
        for term in search_terms:
            try:
                candidate = await client.search(
                    term,
                    item["region_code"],
                    region_names.get(item["region_code"]),
                )
                if candidate.province_name != region_names.get(item["region_code"]):
                    continue
                place = candidate
                break
            except AmapError:
                continue
        if place is None:
            unresolved.append(item["name"])
            continue
        item.update(
            latitude=place.latitude,
            longitude=place.longitude,
            coordinate_verified=True,
            coordinate_source="amap-place-v3",
            provider_place_id=place.provider_id,
            provider_adcode=place.adcode,
        )
        verified += 1
        if delay_seconds:
            await asyncio.sleep(delay_seconds)
    return {"verified": verified, "unresolved": unresolved}


async def main() -> None:
    if not settings.amap_key:
        raise SystemExit("TRAVEL_AMAP_KEY is not configured")
    path = Path(__file__).parents[1] / "data" / "destinations.v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    from app.destinations.amap import AmapClient

    async with httpx.AsyncClient(timeout=15.0) as http:
        summary = await calibrate_payload(
            payload,
            AmapClient(settings.amap_key, http=http),
            delay_seconds=0.08,
        )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
