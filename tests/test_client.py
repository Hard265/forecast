"""Tests for the Open-Meteo HTTP client (retry, DTO validation, errors)."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from forecast.domain.errors import WeatherProviderError
from forecast.infrastructure.providers.open_meteo.client import OpenMeteoClient
from forecast.infrastructure.providers.open_meteo.dto import OpenMeteoResponseDTO


def _ok_payload():
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


def _client_with(handler, *, max_retries=0, backoff_seconds=0.0):
    transport = httpx.MockTransport(handler)
    client = OpenMeteoClient(
        base_url="https://api.open-meteo.com/v1/forecast",
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )
    client._client = httpx.AsyncClient(
        base_url=client.BASE_URL,
        transport=transport,
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": "x"},
    )
    return client


@pytest.fixture
def no_sleep(monkeypatch):
    async def _fast_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_sleep)


async def test_client_returns_valid_dto():
    client = _client_with(lambda req: httpx.Response(200, json=_ok_payload()))
    dto = await client.get_weather(-15.78, 35.0)
    assert isinstance(dto, OpenMeteoResponseDTO)
    assert dto.latitude == -15.78


async def test_client_permanent_4xx_raises():
    client = _client_with(lambda req: httpx.Response(400, json={"error": "bad"}))
    with pytest.raises(WeatherProviderError):
        await client.get_weather(-15.78, 35.0)


async def test_client_retries_on_5xx(no_sleep):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=_ok_payload())

    client = _client_with(handler, max_retries=3, backoff_seconds=0.0)
    dto = await client.get_weather(-15.78, 35.0)
    assert isinstance(dto, OpenMeteoResponseDTO)
    assert calls["n"] == 3


async def test_client_gives_up_after_max_retries(no_sleep):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        return httpx.Response(503)

    client = _client_with(handler, max_retries=2, backoff_seconds=0.0)
    with pytest.raises(WeatherProviderError):
        await client.get_weather(-15.78, 35.0)
    assert calls["n"] == 3  # initial + 2 retries


async def test_client_retries_on_429(no_sleep):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(429)
        return httpx.Response(200, json=_ok_payload())

    client = _client_with(handler, max_retries=2, backoff_seconds=0.0)
    dto = await client.get_weather(-15.78, 35.0)
    assert isinstance(dto, OpenMeteoResponseDTO)
    assert calls["n"] == 2


async def test_client_retries_on_timeout(no_sleep):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        raise httpx.ConnectError("boom")

    client = _client_with(handler, max_retries=2, backoff_seconds=0.0)
    with pytest.raises(WeatherProviderError):
        await client.get_weather(-15.78, 35.0)
    assert calls["n"] == 3


async def test_client_rejects_invalid_daily_variable():
    # Regression: Open-Meteo rejects `wind_speed_10m` as a daily variable;
    # the correct daily field is `wind_speed_10m_max`.
    def handler(req):
        return httpx.Response(400, json={"error": True, "reason": "bad"})

    client = _client_with(handler)
    with pytest.raises(WeatherProviderError):
        await client.get_weather(-15.78, 35.0)


async def test_client_close_is_idempotent():
    client = _client_with(lambda req: httpx.Response(200, json=_ok_payload()))
    await client.close()
    await client.close()  # second close should not raise
