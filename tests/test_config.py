"""Tests for the application configuration and domain errors."""

from __future__ import annotations

import os
from dataclasses import FrozenInstanceError

import pytest

from forecast.application.config import load_settings
from forecast.domain.errors import (
    ConfigurationError,
    ForecastError,
    LocationNotFoundError,
    WeatherCacheError,
    WeatherProviderError,
)


def test_settings_defaults(monkeypatch):
    for key in list(os.environ):
        if key.startswith("FORECAST_") or key.startswith("OPEN_METEO_"):
            monkeypatch.delenv(key, raising=False)

    settings = load_settings()
    assert settings.open_meteo_base_url == "https://api.open-meteo.com/v1/forecast"
    assert settings.open_meteo_timeout_seconds == 10.0
    assert settings.open_meteo_connect_timeout_seconds == 5.0
    assert settings.open_meteo_max_retries == 3
    assert settings.open_meteo_backoff_seconds == 0.5
    assert settings.cache_dir == "data"
    assert settings.sqlite_cache_path == "data/weather.db"
    assert settings.current_cache_ttl_seconds == 600
    assert settings.forecast_cache_ttl_seconds == 1800
    assert settings.default_latitude == -15.7833
    assert settings.default_longitude == 35.0
    assert settings.default_name == "Blantyre"
    assert settings.default_country == "Malawi"
    assert settings.default_region == "Southern"
    assert settings.default_timezone == "Africa/Blantyre"


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("OPEN_METEO_BASE_URL", "https://example.test/v1/forecast")
    monkeypatch.setenv("OPEN_METEO_TIMEOUT_SECONDS", "30.5")
    monkeypatch.setenv("FORECAST_DEFAULT_LATITUDE", "48.85")
    monkeypatch.setenv("FORECAST_DEFAULT_NAME", "Paris")
    monkeypatch.setenv("FORECAST_DEFAULT_TIMEZONE", "UTC")

    settings = load_settings()
    assert settings.open_meteo_base_url == "https://example.test/v1/forecast"
    assert settings.open_meteo_timeout_seconds == 30.5
    assert settings.default_latitude == 48.85
    assert settings.default_name == "Paris"
    assert settings.default_timezone == "UTC"


def test_settings_rejects_bad_float(monkeypatch):
    monkeypatch.setenv("OPEN_METEO_TIMEOUT_SECONDS", "not-a-number")
    with pytest.raises(ValueError):
        load_settings()


def test_settings_rejects_bad_int(monkeypatch):
    monkeypatch.setenv("FORECAST_CURRENT_TTL_SECONDS", "nope")
    with pytest.raises(ValueError):
        load_settings()


def test_settings_is_frozen():
    settings = load_settings()
    with pytest.raises(FrozenInstanceError):
        settings.default_name = "Other"  # type: ignore[misc]


def test_error_hierarchy():
    assert issubclass(WeatherProviderError, ForecastError)
    assert issubclass(WeatherCacheError, ForecastError)
    assert issubclass(LocationNotFoundError, ForecastError)
    assert issubclass(ConfigurationError, ForecastError)


def test_errors_are_raised_and_caught():
    with pytest.raises(WeatherProviderError):
        raise WeatherProviderError("boom")
    with pytest.raises(LocationNotFoundError):
        raise LocationNotFoundError("nope")
    with pytest.raises(WeatherCacheError):
        raise WeatherCacheError("disk full")
    with pytest.raises(ConfigurationError):
        raise ConfigurationError("bad config")
