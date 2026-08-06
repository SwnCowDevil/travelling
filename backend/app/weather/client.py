from datetime import date
from typing import Any

import httpx


class OpenMeteoClient:
    def __init__(self, http: httpx.AsyncClient | None = None) -> None:
        self._http = http

    async def forecast(
        self, *, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> dict[str, Any]:
        return await self._get(
            "https://api.open-meteo.com/v1/forecast",
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

    async def archive(
        self, *, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> dict[str, Any]:
        return await self._get(
            "https://archive-api.open-meteo.com/v1/archive",
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

    async def _get(
        self,
        url: str,
        *,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max"
            ),
            "timezone": "Asia/Shanghai",
        }
        if self._http is not None:
            response = await self._http.get(url, params=params)
        else:
            async with httpx.AsyncClient(timeout=10) as http:
                response = await http.get(url, params=params)
        response.raise_for_status()
        return response.json()
