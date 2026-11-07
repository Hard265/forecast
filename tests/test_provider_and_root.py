"""Tests for the OpenMeteo provider and the composition root."""

from __future__ import annotations

import os

import httpx

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.infrastructure.cache.memory import MemoryWeatherCache
from forecast.infrastructure.cache.tiered import TieredWeatherCache
from forecast.infrastructure.composition_root import (
    create_weather_service,
    default_location,
)
from forecast.infrastructure.providers.open_meteo.client import OpenMeteoClient
from forecast.infrastructure.providers.open_meteo.provider import OpenMeteoProvider


def _sample():
    return {
        "latitude": -15.78,
        "longitude": 35.0,
        "timezone": "Africa/Blantyre",
        "current": {
            "time": "2026-01-01T00:00",
            "temperature_2m": 1.0,
            "apparent_temperature": 1.0,
            "relative_humidity_2m": 1.0,
            "weather_code": 0,
            "is_day": 1,
            "precipitation": 0.0,
            "cloud_cover": 0.0,
            "pressure_msl": 1000.0,
            "wind_speed_10m": 1.0,
            "wind_direction_10m": 1.0,
            "wind_gusts_10m": 1.0,
        },
        "hourly": {
            "time": ["2026-01-01T00:00"],
            "temperature_2m": [1.0],
            "relative_humidity_2m": [1.0],
            "precipitation_probability": [0.0],
            "precipitation": [0.0],
            "weather_code": [0],
            "wind_speed_10m": [1.0],
            "wind_direction_10m": [1.0],
        },
        "daily": {
            "time": ["2026-01-01"],
            "weather_code": [0],
            "temperature_2m_max": [1.0],
            "temperature_2m_min": [1.0],
            "sunrise": ["2026-01-01T06:00"],
            "sunset": ["2026-01-01T18:00"],
            "uv_index_max": [1.0],
            "precipitation_sum": [0.0],
            "precipitation_probability_max": [0.0],
            "wind_speed_10m_max": [1.0],
            "wind_direction_10m_dominant": [1.0],
        },
    }


def _provider():
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=_sample()))
    client = OpenMeteoClient(base_url="https://api.open-meteo.com/v1/forecast")
    client._client = httpx.AsyncClient(
        base_url=client.BASE_URL,
        transport=transport,
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": "x"},
    )
    return OpenMeteoProvider(client=client)


async def test_provider_fetch_current_and_forecast():
    provider = _provider()
    location = __import__(
        "forecast.domain.models.location", fromlist=["Location"]
    ).Location(
        name="X",
        country="Y",
        region=None,
        coordinates=__import__(
            "forecast.domain.models.location", fromlist=["Coordinates"]
        ).Coordinates(latitude=-15.78, longitude=35.0),
        timezone="Africa/Blantyre",
    )
    current = await provider.fetch_current(location)
    forecast = await provider.fetch_forecast(location)
    assert current.temperature.current == 1.0
    assert len(forecast.hourly) == 1
    assert len(forecast.daily) == 1
    await provider.close()


async def test_provider_fetch_alerts_is_empty():
    provider = _provider()
    from forecast.domain.models.location import Coordinates, Location

    location = Location(
        name="X",
        country="Y",
        region=None,
        coordinates=Coordinates(latitude=-15.78, longitude=35.0),
        timezone="Africa/Blantyre",
    )
    assert await provider.fetch_alerts(location) == ()
    await provider.close()


def test_default_location_uses_settings_defaults(monkeypatch):
    for key in list(os.environ):
        if key.startswith("FORECAST_"):
            monkeypatch.delenv(key, raising=False)
    loc = default_location()
    assert loc.name == "Blantyre"
    assert loc.country == "Malawi"
    assert loc.region == "Southern"
    assert loc.coordinates.latitude == -15.7833
    assert loc.coordinates.longitude == 35.0
    assert loc.timezone == "Africa/Blantyre"


def test_default_location_respects_env(monkeypatch):
    monkeypatch.setenv("FORECAST_DEFAULT_NAME", "Paris")
    monkeypatch.setenv("FORECAST_DEFAULT_LATITUDE", "48.85")
    monkeypatch.setenv("FORECAST_DEFAULT_LONGITUDE", "2.35")
    monkeypatch.setenv("FORECAST_DEFAULT_TIMEZONE", "Europe/Paris")
    loc = default_location()
    assert loc.name == "Paris"
    assert loc.coordinates.latitude == 48.85
    assert loc.coordinates.longitude == 2.35
    assert loc.timezone == "Europe/Paris"


def test_create_weather_service_returns_default_service():
    provider = _provider()
    service = create_weather_service(provider=provider)
    assert isinstance(service, DefaultWeatherService)
    assert service._repository._provider is provider
    assert isinstance(service._repository._cache, TieredWeatherCache)
    assert isinstance(service._repository._cache._memory, MemoryWeatherCache)


def test_create_weather_service_uses_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("FORECAST_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("FORECAST_SQLITE_CACHE_PATH", str(tmp_path / "cache" / "w.db"))
    monkeypatch.setenv("FORECAST_CURRENT_TTL_SECONDS", "123")
    monkeypatch.setenv("FORECAST_FORECAST_TTL_SECONDS", "456")

    provider = _provider()
    service = create_weather_service(provider=provider)
    assert service._repository._current_ttl == 123
    assert service._repository._forecast_ttl == 456
    assert (tmp_path / "cache").is_dir()
