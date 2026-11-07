"""Tests for the Open-Meteo provider and repository."""

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


async def test_provider_fetch_current(open_meteo_provider, location):
    provider, calls = open_meteo_provider
    current = await provider.fetch_current(location)
    assert current.temperature.current == 26.0
    assert len(calls) == 1


async def test_provider_fetch_forecast(open_meteo_provider, location):
    provider, calls = open_meteo_provider
    forecast = await provider.fetch_forecast(location)
    assert len(forecast.hourly) == 24
    assert len(forecast.daily) == 1
    assert len(calls) == 1


async def test_provider_fetch_alerts_empty(open_meteo_provider, location):
    provider, _ = open_meteo_provider
    alerts = await provider.fetch_alerts(location)
    assert alerts == ()


async def test_repository_caches_current(location, open_meteo_provider):
    provider, calls = open_meteo_provider
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)

    first = await repo.get_current(location)
    second = await repo.get_current(location)
    assert first is second  # cached object identity
    assert len(calls) == 1


async def test_repository_force_refresh_bypasses_cache(location, open_meteo_provider):
    provider, calls = open_meteo_provider
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)

    await repo.get_current(location)
    await repo.get_current(location, force_refresh=True)
    assert len(calls) == 2


async def test_repository_forecast_cache_hit(location, open_meteo_provider):
    provider, calls = open_meteo_provider
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)

    first = await repo.get_forecast(location)
    second = await repo.get_forecast(location)
    assert first is second
    assert len(calls) == 1


async def test_repository_alerts_not_cached(location, open_meteo_provider):
    provider, calls = open_meteo_provider
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)

    first = await repo.get_alerts(location)
    second = await repo.get_alerts(location)
    assert first == second == ()
    # Alerts bypass the HTTP client (Open-Meteo has no alert endpoint here),
    # so no outbound calls are expected.
    assert len(calls) == 0


async def test_repository_snapshot(location, open_meteo_provider):
    provider, calls = open_meteo_provider
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)

    snapshot = await repo.get_snapshot(location)
    assert snapshot.current.temperature.current == 26.0
    assert len(snapshot.forecast.hourly) == 24
    assert snapshot.alerts == ()
    assert snapshot.fetched_at is not None
    # Snapshot fetches current + forecast (alerts do not hit the HTTP client).
    assert len(calls) == 2


async def test_repository_cache_keys_include_coordinates(location, open_meteo_provider):
    provider, calls = open_meteo_provider
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)

    await repo.get_current(location)
    key = (
        f"weather:current:{location.coordinates.latitude}:"
        f"{location.coordinates.longitude}"
    )
    assert await cache._memory.get(key) is not None
