from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.footprints.schemas import FootprintStatus
from app.map.schemas import MapSummaryResponse
from app.map.service import build_map_summary
from app.map.pack import MAP_PACK_PATH, metadata_for

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/pack")
def map_pack_metadata() -> dict[str, str | int]:
    if not MAP_PACK_PATH.is_file():
        raise HTTPException(status_code=404, detail="地图包尚未生成，请先执行 build_map_pack")
    metadata = metadata_for(MAP_PACK_PATH)
    return {"version": metadata.version, "byte_size": metadata.byte_size, "md5": metadata.md5,
            "download_path": "/map/pack/download"}


@router.get("/pack/download")
def download_map_pack() -> FileResponse:
    if not MAP_PACK_PATH.is_file():
        raise HTTPException(status_code=404, detail="地图包尚未生成，请先执行 build_map_pack")
    return FileResponse(MAP_PACK_PATH, media_type="application/json", filename=MAP_PACK_PATH.name)


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
