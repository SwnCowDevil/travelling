from sqlalchemy import func, select
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.destinations.models import AdministrativeRegion, Destination
from app.footprints.models import DestinationStatus, RegionStatus
from app.map.amap import AmapDistrictClient, AmapDistrictError
from app.map.models import RegionBoundary
from app.map.schemas import RegionMapSummary
from app.visits.models import VisitRecord

MAX_MAP_PATHS_PER_REGION = 4
MAX_MAP_POINTS_PER_REGION = 80


@dataclass(frozen=True)
class SyncResult:
    regions_created: int = 0
    boundaries_cached: int = 0
    failures: int = 0


def _save_boundary(session: Session, code: str, longitude: float, latitude: float, polygons: list[list[list[float]]]) -> bool:
    boundary = session.get(RegionBoundary, code)
    if boundary is not None and boundary.polygons:
        return False
    if boundary is not None:
        boundary.center_longitude = longitude
        boundary.center_latitude = latitude
        boundary.polygons = polygons
        boundary.source = "amap"
        return True
    session.add(RegionBoundary(
        region_code=code, center_longitude=longitude, center_latitude=latitude,
        polygons=polygons, source="amap",
    ))
    return True


def _has_usable_boundary(session: Session, code: str) -> bool:
    boundary = session.get(RegionBoundary, code)
    return bool(boundary and boundary.polygons)


def sync_region_layer(
    session: Session, client: AmapDistrictClient, parent_code: str | None
) -> SyncResult:
    parent_codes = ([parent_code] if parent_code else [
        region.code for region in session.scalars(
            select(AdministrativeRegion).where(AdministrativeRegion.level == "province")
        )
    ])
    regions_created = 0
    boundaries_cached = 0
    failures = 0
    for code in parent_codes:
        known_cities = list(session.scalars(select(AdministrativeRegion).where(
            AdministrativeRegion.parent_code == code,
            AdministrativeRegion.level == "city",
        )))
        if not _has_usable_boundary(session, code) or not known_cities:
            try:
                region = client.fetch_region(code)
            except AmapDistrictError:
                failures += 1
                continue
            boundaries_cached += int(_save_boundary(
                session, region.code, region.center_longitude, region.center_latitude, region.polygons
            ))
            for child in region.children:
                if child.level != "city" or session.get(AdministrativeRegion, child.code):
                    continue
                session.add(AdministrativeRegion(
                    code=child.code, name=child.name, level=child.level, parent_code=region.code
                ))
                regions_created += 1
    session.commit()
    if parent_code:
        for child in session.scalars(select(AdministrativeRegion).where(
            AdministrativeRegion.parent_code == parent_code,
            AdministrativeRegion.level == "city",
        )):
            if _has_usable_boundary(session, child.code):
                continue
            try:
                region = client.fetch_region(child.code)
            except AmapDistrictError:
                failures += 1
                continue
            boundaries_cached += int(_save_boundary(
                session, region.code, region.center_longitude, region.center_latitude, region.polygons
            ))
        session.commit()
    return SyncResult(
        regions_created=regions_created, boundaries_cached=boundaries_cached, failures=failures
    )


def resolve_map_status(direct_status: str | None, status_counts: dict[str, int]) -> str | None:
    for status in ("visited", "revisit", "want", "avoid"):
        if direct_status == status or status_counts.get(status, 0) > 0:
            return status
    return None


def _polygon_area(path: list[list[float]]) -> float:
    return abs(sum(
        point[0] * path[(index + 1) % len(path)][1]
        - path[(index + 1) % len(path)][0] * point[1]
        for index, point in enumerate(path)
    ))


def _sample_path(path: list[list[float]], maximum: int) -> list[list[float]]:
    if len(path) <= maximum:
        return path
    return [path[round(index * (len(path) - 1) / (maximum - 1))] for index in range(maximum)]


def simplify_map_polygons(polygons: list[list[list[float]]]) -> list[list[list[float]]]:
    valid = [path for path in polygons if len(path) >= 3]
    selected = sorted(valid, key=_polygon_area, reverse=True)[:MAX_MAP_PATHS_PER_REGION]
    if not selected:
        return []
    base_points = 3 * len(selected)
    remaining = MAX_MAP_POINTS_PER_REGION - base_points
    excess_total = sum(max(0, len(path) - 3) for path in selected)
    return [
        _sample_path(
            path,
            min(len(path), 3 + int(remaining * max(0, len(path) - 3) / excess_total))
            if excess_total else len(path),
        )
        for path in selected
    ]


def build_map_summary(
    session: Session,
    user_id: int,
    *,
    parent_code: str | None,
    status: str | None = None,
) -> list[RegionMapSummary]:
    regions = list(session.scalars(select(AdministrativeRegion)).all())
    by_code = {region.code: region for region in regions}
    children = [region for region in regions if region.parent_code == parent_code]
    destination_regions = {
        destination_id: (province_code, city_code)
        for destination_id, province_code, city_code in session.execute(
            select(Destination.id, Destination.region_code, Destination.city_region_code)
        ).all()
    }
    statuses = session.execute(
        select(DestinationStatus.destination_id, DestinationStatus.status).where(
            DestinationStatus.user_id == user_id
        )
    ).all()
    visit_counts = dict(session.execute(
        select(VisitRecord.destination_id, func.count(VisitRecord.id))
        .where(VisitRecord.user_id == user_id)
        .group_by(VisitRecord.destination_id)
    ).all())
    direct = dict(session.execute(
        select(RegionStatus.region_code, RegionStatus.status).where(
            RegionStatus.user_id == user_id
        )
    ).all())

    aggregates: dict[str, dict[str, int]] = {}
    visits_by_region: dict[str, int] = {}
    for destination_id, footprint_status in statuses:
        region_codes = destination_regions.get(destination_id)
        region_code = region_codes[1] or region_codes[0] if region_codes else None
        while region_code:
            counts = aggregates.setdefault(region_code, {})
            counts[footprint_status] = counts.get(footprint_status, 0) + 1
            visits_by_region[region_code] = (
                visits_by_region.get(region_code, 0) + int(visit_counts.get(destination_id, 0))
            )
            region = by_code.get(region_code)
            region_code = region.parent_code if region else None

    boundaries = {
        boundary.region_code: boundary
        for boundary in session.scalars(select(RegionBoundary)).all()
    }
    result = []
    for region in children:
        boundary = boundaries.get(region.code)
        counts = aggregates.get(region.code, {})
        direct_status = direct.get(region.code)
        result.append(RegionMapSummary(
            region_code=region.code, name=region.name, level=region.level,
            direct_status=direct_status, status_counts=counts,
            visit_count=visits_by_region.get(region.code, 0),
            center=[boundary.center_longitude, boundary.center_latitude] if boundary else None,
            polygons=[],
            map_status=resolve_map_status(direct_status, counts),
        ))
    if status:
        result = [
            item for item in result
            if item.direct_status == status or item.status_counts.get(status, 0) > 0
        ]
    return sorted(result, key=lambda item: item.region_code)
