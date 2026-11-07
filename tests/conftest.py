"""Shared fixtures for the forecast test suite."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from forecast.domain.models.location import Coordinates, Location
from forecast.infrastructure.cache.memory import MemoryWeatherCache
from forecast.infrastructure.cache.tiered import TieredWeatherCache
from forecast.infrastructure.providers.open_meteo.client import OpenMeteoClient
from forecast.infrastructure.providers.open_meteo.mapper import OpenMeteoMapper
from forecast.infrastructure.providers.open_meteo.provider import OpenMeteoProvider

SAMPLE_PAYLOAD: dict[str, Any] = {
    "latitude": -15.78,
    "longitude": 35.0,
    "timezone": "Africa/Blantyre",
    "current": {
        "time": "2026-11-07T10:00",
        "temperature_2m": 26.0,
        "apparent_temperature": 27.0,
        "relative_humidity_2m": 60.0,
        "weather_code": 1,
        "is_day": 1,
        "precipitation": 0.0,
        "cloud_cover": 25.0,
        "pressure_msl": 1010.0,
        "wind_speed_10m": 5.0,
        "wind_direction_10m": 180.0,
        "wind_gusts_10m": 7.0,
    },
    "hourly": {
        "time": [f"2026-11-07T{h:02d}:00" for h in range(24)],
        "temperature_2m": [26.0 + (h % 5) for h in range(24)],
        "relative_humidity_2m": [60.0] * 24,
        "precipitation_probability": [10.0 + h for h in range(24)],
        "precipitation": [0.0] * 24,
        "weather_code": [1 if h < 12 else 2 for h in range(24)],
        "wind_speed_10m": [5.0] * 24,
        "wind_direction_10m": [180.0] * 24,
    },
    "daily": {
        "time": ["2026-11-07"],
        "weather_code": [1],
        "temperature_2m_max": [28.0],
        "temperature_2m_min": [20.0],
        "sunrise": ["2026-11-07T05:30"],
        "sunset": ["2026-11-07T18:00"],
        "uv_index_max": [6.0],
        "precipitation_sum": [0.0],
        "precipitation_probability_max": [20.0],
        "wind_speed_10m_max": [5.0],
        "wind_direction_10m_dominant": [180.0],
    },
}


@pytest.fixture
def sample_payload() -> dict[str, Any]:
    return json.loads(json.dumps(SAMPLE_PAYLOAD))


@pytest.fixture
def location() -> Location:
    return Location(
        name="Blantyre",
        country="Malawi",
        region="Southern",
        coordinates=Coordinates(latitude=-15.78, longitude=35.0),
        timezone="Africa/Blantyre",
    )


@pytest.fixture
def mock_transport():
    """Return a factory that builds an httpx MockTransport returning a payload."""
    calls: list[httpx.Request] = []

    def factory(payload: dict[str, Any] | None = None, status: int = 200):
        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(status, json=payload or SAMPLE_PAYLOAD)

        transport = httpx.MockTransport(handler)
        return transport, calls

    return factory


@pytest.fixture
def open_meteo_provider(mock_transport):
    transport, calls = mock_transport()
    client = OpenMeteoClient(base_url="https://api.open-meteo.com/v1/forecast")
    client._client = httpx.AsyncClient(
        base_url=client.BASE_URL,
        transport=transport,
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": "ForecastCli/1.0"},
    )
    return OpenMeteoProvider(client=client, mapper=OpenMeteoMapper()), calls


@pytest.fixture
def memory_cache() -> MemoryWeatherCache:
    return MemoryWeatherCache()


@pytest.fixture
def tiered_cache(memory_cache) -> TieredWeatherCache:
    return TieredWeatherCache(memory=memory_cache, persistent=MemoryWeatherCache())


@pytest.fixture
def sqlite_cache(tmp_path):
    from forecast.infrastructure.cache.sqlite import SQLiteWeatherCache

    return SQLiteWeatherCache(database_path=str(tmp_path / "test_weather.db"))
