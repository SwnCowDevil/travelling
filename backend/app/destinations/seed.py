import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.destinations.models import AdministrativeRegion, Destination


class SeedValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SeedResult:
    created: int
    updated: int


def _validate_destination(item: dict[str, Any], region_codes: set[str]) -> None:
    required = {"code", "name", "latitude", "longitude", "region_code"}
    missing = required - item.keys()
    if missing:
        raise SeedValidationError(f"missing fields: {', '.join(sorted(missing))}")
    if not -90 <= float(item["latitude"]) <= 90:
        raise SeedValidationError("latitude must be between -90 and 90")
    if not -180 <= float(item["longitude"]) <= 180:
        raise SeedValidationError("longitude must be between -180 and 180")
    if item["region_code"] not in region_codes:
        raise SeedValidationError(f"unknown region: {item['region_code']}")
    months = item.get("suitable_months", [])
    if any(not isinstance(month, int) or month < 1 or month > 12 for month in months):
        raise SeedValidationError("month must be an integer from 1 to 12")


def seed_destinations(session: Session, path: Path) -> SeedResult:
    payload = json.loads(path.read_text(encoding="utf-8"))
    version = str(payload["version"])

    for item in payload.get("regions", []):
        region = session.get(AdministrativeRegion, item["code"])
        if region is None:
            session.add(AdministrativeRegion(**item))
        else:
            region.name = item["name"]
            region.level = item["level"]
            region.parent_code = item.get("parent_code")
    session.flush()

    region_codes = set(session.scalars(select(AdministrativeRegion.code)))
    created = 0
    updated = 0
    for item in payload["destinations"]:
        _validate_destination(item, region_codes)
        values = {
            "summary": "",
            "categories": [],
            "suitable_months": [],
            "season_tags": [],
            "crowd_tags": [],
            "transport_modes": [],
            "climate": {},
            "quality_score": 0.5,
            "coordinate_verified": False,
            "coordinate_source": "approximate",
            **item,
            "data_version": version,
        }
        destination = session.scalar(
            select(Destination).where(Destination.code == item["code"])
        )
        if destination is None:
            session.add(Destination(**values))
            created += 1
        else:
            for key, value in values.items():
                setattr(destination, key, value)
            updated += 1
    session.commit()
    return SeedResult(created=created, updated=updated)
