from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class WeatherDestination(Protocol):
    id: int
    latitude: float
    longitude: float
    climate: dict[str, Any]


class DailyWeather(BaseModel):
    date: date
    temperature_max: float | None = None
    temperature_min: float | None = None
    precipitation_probability: int | None = None
    weather_code: int | None = None


class WeatherResult(BaseModel):
    kind: Literal["forecast", "climate_reference", "local_climate"]
    source: Literal["open_meteo", "local_climate"]
    updated_at: datetime
    daily: list[DailyWeather] = Field(default_factory=list)
    climate: dict[str, Any] = Field(default_factory=dict)


class WeatherService:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def get(
        self, destination: WeatherDestination, start_date: date, end_date: date
    ) -> WeatherResult:
        now = datetime.now(timezone.utc)
        if start_date > date.today() + timedelta(days=16):
            return WeatherResult(
                kind="climate_reference",
                source="local_climate",
                updated_at=now,
                climate=destination.climate,
            )
        try:
            payload = await self.client.forecast(
                latitude=destination.latitude,
                longitude=destination.longitude,
                start_date=start_date,
                end_date=end_date,
            )
            return WeatherResult(
                kind="forecast",
                source="open_meteo",
                updated_at=now,
                daily=self._daily(payload),
            )
        except Exception:
            return WeatherResult(
                kind="local_climate",
                source="local_climate",
                updated_at=now,
                climate=destination.climate,
            )

    @staticmethod
    def _daily(payload: dict[str, Any]) -> list[DailyWeather]:
        daily = payload["daily"]
        dates = daily["time"]
        values = []
        for index, day in enumerate(dates):
            values.append(DailyWeather(
                date=day,
                temperature_max=_at(daily, "temperature_2m_max", index),
                temperature_min=_at(daily, "temperature_2m_min", index),
                precipitation_probability=_at(
                    daily, "precipitation_probability_max", index
                ),
                weather_code=_at(daily, "weather_code", index),
            ))
        return values


def _at(values: dict[str, Any], key: str, index: int) -> Any:
    items = values.get(key, [])
    return items[index] if index < len(items) else None
