from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai.router import get_current_user_id
from app.core.config import settings
from app.locations.amap import (
    AmapConfigurationError,
    AmapReverseClient,
    AmapReverseError,
    ResolvedLocation,
)
from app.locations.schemas import ResolvedLocationResponse

router = APIRouter(prefix="/locations", tags=["locations"])


async def get_reverse_client() -> AsyncIterator[AmapReverseClient]:
    async with httpx.AsyncClient(timeout=10) as http:
        yield AmapReverseClient(settings.amap_key, http=http)


@router.get("/reverse-geocode", response_model=ResolvedLocationResponse)
async def reverse_geocode(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    _user_id: int = Depends(get_current_user_id),
    client: AmapReverseClient = Depends(get_reverse_client),
) -> ResolvedLocation:
    try:
        return await client.reverse(latitude, longitude)
    except AmapConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "LOCATION_SERVICE_UNAVAILABLE",
                "message": "地点识别服务未配置",
            },
        ) from exc
    except AmapReverseError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "LOCATION_LOOKUP_FAILED",
                "message": "暂时无法识别地点名称",
            },
        ) from exc
