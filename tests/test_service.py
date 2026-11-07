"""Tests for the application service layer."""

from datetime import UTC

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Coordinates, Location
from forecast.infrastructure.cache.memory import MemoryWeatherCache
from forecast.infrastructure.cache.tiered import TieredWeatherCache
from forecast.infrastructure.repositories.weather_repository import (
    DefaultWeatherRepository,
)


def _location() -> Location:
    return Location(
        name="Blantyre",
        country="Malawi",
        region="Southern",
        coordinates=Coordinates(latitude=-15.78, longitude=35.0),
        timezone="Africa/Blantyre",
    )


def _service(open_meteo_provider) -> DefaultWeatherService:
    provider, _ = open_meteo_provider
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)
    return DefaultWeatherService(repo)


async def test_service_get_current_weather(open_meteo_provider, location):
    service = _service(open_meteo_provider)
    current = await service.get_current_weather(location)
    assert current.temperature.current == 26.0


async def test_service_get_forecast(open_meteo_provider, location):
    service = _service(open_meteo_provider)
    forecast = await service.get_forecast(location)
    assert len(forecast.hourly) == 24
    assert len(forecast.daily) == 1


async def test_service_get_weather_dashboard(open_meteo_provider, location):
    service = _service(open_meteo_provider)
    snapshot = await service.get_weather_dashboard(location)
    assert snapshot.current.temperature.current == 26.0
    assert len(snapshot.forecast.hourly) == 24
    assert snapshot.alerts == ()
    assert snapshot.fetched_at.tzinfo == UTC


async def test_service_dashboard_uses_single_provider_trip(
    open_meteo_provider, location
):
    provider, calls = open_meteo_provider
    service = _service(open_meteo_provider)
    await service.get_weather_dashboard(location)
    # A single upstream request now provides current + forecast.
    assert len(calls) == 1


async def test_service_refresh_bypasses_cache(open_meteo_provider, location):
    provider, calls = open_meteo_provider
    service = _service(open_meteo_provider)

    await service.get_current_weather(location)
    await service.get_current_weather(location, refresh=True)
    assert len(calls) == 2


async def test_service_cache_hit_does_not_rehit_provider(open_meteo_provider, location):
    provider, calls = open_meteo_provider
    service = _service(open_meteo_provider)

    await service.get_current_weather(location)
    await service.get_current_weather(location)
    assert len(calls) == 1
