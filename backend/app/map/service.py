from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.destinations.models import AdministrativeRegion, Destination
from app.footprints.models import DestinationStatus, RegionStatus
from app.map.schemas import RegionMapSummary
from app.visits.models import VisitRecord


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
    destination_regions = dict(session.execute(
        select(Destination.id, Destination.region_code)
    ).all())
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
        region_code = destination_regions.get(destination_id)
        while region_code:
            counts = aggregates.setdefault(region_code, {})
            counts[footprint_status] = counts.get(footprint_status, 0) + 1
            visits_by_region[region_code] = (
                visits_by_region.get(region_code, 0) + int(visit_counts.get(destination_id, 0))
            )
            region = by_code.get(region_code)
            region_code = region.parent_code if region else None

    result = [RegionMapSummary(
        region_code=region.code,
        name=region.name,
        level=region.level,
        direct_status=direct.get(region.code),
        status_counts=aggregates.get(region.code, {}),
        visit_count=visits_by_region.get(region.code, 0),
    ) for region in children]
    if status:
        result = [
            item for item in result
            if item.direct_status == status or item.status_counts.get(status, 0) > 0
        ]
    return sorted(result, key=lambda item: item.region_code)
