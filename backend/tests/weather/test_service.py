from datetime import date, timedelta

import pytest

from app.weather.service import WeatherService


class DestinationStub:
    id = 1
    latitude = 30.25
    longitude = 120.15
    climate = {"summary": "春季温和多雨", "packing": ["雨伞", "薄外套"]}


@pytest.mark.asyncio
async def test_near_date_returns_forecast() -> None:
    class Client:
        async def forecast(self, **_kwargs):
            return {
                "daily": {
                    "time": [date.today().isoformat()],
                    "temperature_2m_max": [22.0],
                    "temperature_2m_min": [14.0],
                    "precipitation_probability_max": [40],
                    "weather_code": [3],
                }
            }

    result = await WeatherService(Client()).get(
        DestinationStub(), date.today(), date.today() + timedelta(days=2)
    )

    assert result.kind == "forecast"
    assert result.source == "open_meteo"
    assert result.daily[0].temperature_max == 22.0


@pytest.mark.asyncio
async def test_far_future_returns_climate_reference_without_live_call() -> None:
    class Client:
        async def forecast(self, **_kwargs):
            raise AssertionError("far-future request should not call forecast")

    start = date.today() + timedelta(days=90)
    result = await WeatherService(Client()).get(
        DestinationStub(), start, start + timedelta(days=3)
    )

    assert result.kind == "climate_reference"
    assert result.source == "local_climate"
    assert result.climate["summary"] == "春季温和多雨"


@pytest.mark.asyncio
async def test_open_meteo_error_falls_back_to_local_climate() -> None:
    class Client:
        async def forecast(self, **_kwargs):
            raise RuntimeError("network unavailable")

    result = await WeatherService(Client()).get(
        DestinationStub(), date.today(), date.today() + timedelta(days=1)
    )

    assert result.kind == "local_climate"
    assert result.source == "local_climate"
    assert result.climate["packing"] == ["雨伞", "薄外套"]
