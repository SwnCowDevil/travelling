import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.core.config import settings
from app.custom_destinations.schemas import CustomDestinationCandidate, CustomDestinationRead, CustomDestinationSearchResponse
from app.custom_destinations.service import get_custom_destination, save_custom_destination
from app.db.session import get_db
from app.destinations.amap import AmapError

router = APIRouter(prefix="/custom-destinations", tags=["custom-destinations"])


def _read(item) -> CustomDestinationRead:
    return CustomDestinationRead.model_validate(item, from_attributes=True)


@router.get("/search", response_model=CustomDestinationSearchResponse)
async def search_custom_destinations(keyword: str = Query(min_length=2, max_length=100), _user_id: int = Depends(get_current_user_id)) -> CustomDestinationSearchResponse:
    if not settings.amap_key:
        raise HTTPException(503, detail={"code": "AMAP_NOT_CONFIGURED", "message": "地点搜索暂不可用"})
    try:
        async with httpx.AsyncClient(timeout=12) as http:
            response = await http.get("https://restapi.amap.com/v3/place/text", params={"key": settings.amap_key, "keywords": keyword, "offset": 5, "page": 1, "extensions": "base"})
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "1":
            raise AmapError(str(payload.get("info", "request failed")))
        items=[]
        for poi in payload.get("pois", []):
            try:
                longitude, latitude = map(float, poi["location"].split(","))
                items.append(CustomDestinationCandidate(amap_poi_id=str(poi["id"]), name=str(poi["name"]), address=str(poi.get("address") or ""), region_name="".join(str(poi.get(key) or "") for key in ("pname", "cityname", "adname")), latitude=latitude, longitude=longitude))
            except (KeyError, TypeError, ValueError):
                continue
        return CustomDestinationSearchResponse(items=items)
    except (httpx.HTTPError, AmapError) as exc:
        raise HTTPException(502, detail={"code": "AMAP_SEARCH_FAILED", "message": "地点搜索暂不可用"}) from exc


@router.post("", response_model=CustomDestinationRead, status_code=201)
def create_custom_destination(body: CustomDestinationCandidate, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> CustomDestinationRead:
    item, _ = save_custom_destination(session, user_id, body.model_dump())
    return _read(item)


@router.get("/{destination_id}", response_model=CustomDestinationRead)
def read_custom_destination(destination_id: int, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> CustomDestinationRead:
    item = get_custom_destination(session, user_id, destination_id)
    if item is None:
        raise HTTPException(404, detail={"code": "CUSTOM_DESTINATION_NOT_FOUND"})
    return _read(item)
