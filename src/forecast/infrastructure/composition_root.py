"""Composition root: wires infrastructure adapters to application services.

This is the only place where concrete implementations are referenced. Keeping
dependency injection in one module makes the wiring explicit and testable.
"""

from __future__ import annotations

import os
from pathlib import Path

from forecast.application.config import Settings, load_settings
from forecast.application.repositories.user_preferences import UserPreferencesRepository
from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Coordinates, Location
from forecast.infrastructure.cache.memory import MemoryWeatherCache
from forecast.infrastructure.cache.sqlite import SQLiteWeatherCache
from forecast.infrastructure.cache.tiered import TieredWeatherCache
from forecast.infrastructure.providers.open_meteo.client import OpenMeteoClient
from forecast.infrastructure.providers.open_meteo.geocoding import GeocodingClient
from forecast.infrastructure.providers.open_meteo.provider import OpenMeteoProvider
from forecast.infrastructure.repositories.sqlite_user_preferences import (
    SqliteUserPreferencesRepository,
)
from forecast.infrastructure.repositories.weather_repository import (
    DefaultWeatherRepository,
)


def create_weather_service(
    settings: Settings | None = None,
    *,
    provider: OpenMeteoProvider | None = None,
) -> DefaultWeatherService:
    settings = settings or load_settings()

    if provider is None:
        client = OpenMeteoClient(
            base_url=settings.open_meteo_base_url,
            timeout=settings.open_meteo_timeout_seconds,
            connect_timeout=settings.open_meteo_connect_timeout_seconds,
            max_retries=settings.open_meteo_max_retries,
            backoff_seconds=settings.open_meteo_backoff_seconds,
        )
        provider = OpenMeteoProvider(client=client)

    cache_dir = Path(settings.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    memory_cache = MemoryWeatherCache()
    sqlite_cache = SQLiteWeatherCache(database_path=settings.sqlite_cache_path)
    cache = TieredWeatherCache(memory=memory_cache, persistent=sqlite_cache)

    repository = DefaultWeatherRepository(
        provider=provider,
        cache=cache,
        current_ttl_seconds=settings.current_cache_ttl_seconds,
        forecast_ttl_seconds=settings.forecast_cache_ttl_seconds,
    )

    return DefaultWeatherService(repository=repository)


def create_user_preferences_repository(
    settings: Settings | None = None,
) -> UserPreferencesRepository:
    settings = settings or load_settings()
    return SqliteUserPreferencesRepository(database_path=settings.sqlite_cache_path)


def create_geocoding_client(settings: Settings | None = None) -> GeocodingClient:
    settings = settings or load_settings()
    return GeocodingClient(base_url=settings.geocoding_base_url)


def default_location(settings: Settings | None = None) -> Location:
    settings = settings or load_settings()
    return Location(
        name=settings.default_name,
        country=settings.default_country,
        region=settings.default_region,
        coordinates=Coordinates(
            latitude=settings.default_latitude,
            longitude=settings.default_longitude,
        ),
        timezone=settings.default_timezone,
    )


def get_data_dir() -> Path:
    """Return the writable data directory, creating it if necessary."""
    data_dir = Path(os.environ.get("FORECAST_CACHE_DIR", os.environ.get("FORECAST_DATA_DIR", "data")))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def ensure_data_dir() -> Path:
    """Backwards-compatible alias used by the app entrypoint."""
    return get_data_dir()
