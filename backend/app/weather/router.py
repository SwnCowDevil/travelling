from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.router import get_current_user_id
from app.db.session import get_db
from app.destinations.models import Destination
from app.custom_destinations.service import get_custom_destination
from app.weather.client import OpenMeteoClient
from app.weather.service import WeatherResult, WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_service() -> WeatherService:
    return WeatherService(OpenMeteoClient())


@router.get("/{destination_id}", response_model=WeatherResult)
async def get_weather(
    destination_id: int,
    start_date: date = Query(default_factory=date.today),
    end_date: date | None = None,
    _user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    service: WeatherService = Depends(get_weather_service),
) -> WeatherResult:
    destination = session.get(Destination, destination_id)
    if destination is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DESTINATION_NOT_FOUND", "message": "目的地不存在"},
        )
    resolved_end = end_date or start_date + timedelta(days=2)
    if resolved_end < start_date or (resolved_end - start_date).days > 16:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_DATE_RANGE", "message": "天气日期范围无效"},
        )
    return await service.get(destination, start_date, resolved_end)


@router.get("/custom/{destination_id}", response_model=WeatherResult)
async def get_custom_weather(
    destination_id: int,
    start_date: date = Query(default_factory=date.today),
    end_date: date | None = None,
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
    service: WeatherService = Depends(get_weather_service),
) -> WeatherResult:
    destination = get_custom_destination(session, user_id, destination_id)
    if destination is None:
        raise HTTPException(404, detail={"code": "CUSTOM_DESTINATION_NOT_FOUND"})
    resolved_end = end_date or start_date + timedelta(days=2)
    if resolved_end < start_date or (resolved_end - start_date).days > 16:
        raise HTTPException(422, detail={"code": "INVALID_DATE_RANGE", "message": "天气日期范围无效"})
    return await service.get(destination, start_date, resolved_end)
