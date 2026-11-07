"""Application configuration.

Settings are loaded from environment variables with sensible defaults so the
app can run identically in dev, test, and production. All values are typed and
validated at startup via :func:`load_settings`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, str(default))
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a float, got {raw!r}") from exc


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an int, got {raw!r}") from exc


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, str(default)).strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean, got {raw!r}")


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed configuration for the forecast application."""

    open_meteo_base_url: str
    open_meteo_timeout_seconds: float
    open_meteo_connect_timeout_seconds: float
    open_meteo_max_retries: int
    open_meteo_backoff_seconds: float

    geocoding_base_url: str
    bundled_cities_path: str

    cache_dir: str
    sqlite_cache_path: str
    current_cache_ttl_seconds: int
    forecast_cache_ttl_seconds: int

    default_latitude: float
    default_longitude: float
    default_name: str
    default_country: str
    default_region: str
    default_timezone: str


def load_settings() -> Settings:
    """Build a :class:`Settings` instance from the current environment."""
    return Settings(
        open_meteo_base_url=_env(
            "OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast"
        ),
        open_meteo_timeout_seconds=_env_float("OPEN_METEO_TIMEOUT_SECONDS", 10.0),
        open_meteo_connect_timeout_seconds=_env_float(
            "OPEN_METEO_CONNECT_TIMEOUT_SECONDS", 5.0
        ),
        open_meteo_max_retries=_env_int("OPEN_METEO_MAX_RETRIES", 3),
        open_meteo_backoff_seconds=_env_float("OPEN_METEO_BACKOFF_SECONDS", 0.5),
        geocoding_base_url=_env(
            "OPEN_METEO_GEOCODING_BASE_URL",
            "https://geocoding-api.open-meteo.com/v1/search",
        ),
        bundled_cities_path=_env("FORECAST_BUNDLED_CITIES_PATH", "data/cities.json"),
        cache_dir=_env("FORECAST_CACHE_DIR", "data"),
        sqlite_cache_path=_env("FORECAST_SQLITE_CACHE_PATH", "data/weather.db"),
        current_cache_ttl_seconds=_env_int("FORECAST_CURRENT_TTL_SECONDS", 600),
        forecast_cache_ttl_seconds=_env_int("FORECAST_FORECAST_TTL_SECONDS", 1800),
        default_latitude=_env_float("FORECAST_DEFAULT_LATITUDE", -15.7833),
        default_longitude=_env_float("FORECAST_DEFAULT_LONGITUDE", 35.0),
        default_name=_env("FORECAST_DEFAULT_NAME", "Blantyre"),
        default_country=_env("FORECAST_DEFAULT_COUNTRY", "Malawi"),
        default_region=_env("FORECAST_DEFAULT_REGION", "Southern"),
        default_timezone=_env("FORECAST_DEFAULT_TIMEZONE", "Africa/Blantyre"),
    )
