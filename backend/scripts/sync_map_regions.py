import argparse
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.destinations.models import AdministrativeRegion, Destination
from app.map.amap import AmapDistrictClient
from app.map.service import sync_region_layer


@dataclass(frozen=True)
class MapSyncSummary:
    regions_created: int
    boundaries_cached: int
    unmatched_destinations: int


def _city_code(adcode: str | None) -> str | None:
    digits = str(adcode or "").strip()
    if len(digits) != 6 or not digits.isdigit():
        return None
    candidate = f"{digits[:4]}00"
    return None if candidate == f"{digits[:2]}0000" else candidate


def _assign_city_regions(session: Session) -> int:
    unmatched = 0
    for destination in session.scalars(select(Destination)).all():
        candidate = _city_code(destination.provider_adcode)
        city = session.get(AdministrativeRegion, candidate) if candidate else None
        if city is None or city.parent_code != destination.region_code:
            unmatched += 1
            continue
        destination.city_region_code = city.code
    session.commit()
    return unmatched


def run_sync(session: Session, api_key: str | None, province_codes: list[str]) -> MapSyncSummary:
    if not api_key:
        raise SystemExit("TRAVEL_AMAP_KEY is required")
    regions_created = 0
    boundaries_cached = 0
    with httpx.Client(timeout=15.0) as http:
        client = AmapDistrictClient(api_key, http=http)
        for province_code in province_codes:
            result = sync_region_layer(session, client, province_code)
            regions_created += result.regions_created
            boundaries_cached += result.boundaries_cached
    return MapSyncSummary(
        regions_created=regions_created,
        boundaries_cached=boundaries_cached,
        unmatched_destinations=_assign_city_regions(session),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache AMap province and city boundaries")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--province", action="append", dest="provinces")
    group.add_argument("--all-provinces", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as session:
        province_codes = args.provinces or list(session.scalars(select(AdministrativeRegion.code).where(
            AdministrativeRegion.level == "province"
        )))
        summary = run_sync(session, settings.amap_key, province_codes)
    print(
        f"regions={summary.regions_created} boundaries={summary.boundaries_cached} "
        f"unmatched_destinations={summary.unmatched_destinations}"
    )


if __name__ == "__main__":
    main()
