from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.footprints.schemas import FootprintStatus
from app.map.schemas import MapSummaryResponse
from app.map.service import build_map_summary

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/summary", response_model=MapSummaryResponse)
def map_summary(
    parent_code: str | None = None,
    status: FootprintStatus | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> MapSummaryResponse:
    items = build_map_summary(
        session,
        user_id,
        parent_code=parent_code,
        status=status.value if status else None,
    )
    return MapSummaryResponse(
        items=items,
        geometry_available=any(bool(item.polygons) for item in items),
    )
