"""Tests for the Textual UI widgets and app.

These tests run the app headless via textual's `run_test()` pilot, which is the
documented approach for testing Textual applications without a real terminal.
"""

from __future__ import annotations

import httpx
import pytest
from textual.widgets import DataTable, Digits, Static

from forecast.app import ForecastApp
from forecast.application.services.weather_service import DefaultWeatherService
from forecast.infrastructure.cache.memory import MemoryWeatherCache
from forecast.infrastructure.cache.tiered import TieredWeatherCache
from forecast.infrastructure.providers.open_meteo.client import OpenMeteoClient
from forecast.infrastructure.providers.open_meteo.provider import OpenMeteoProvider
from forecast.infrastructure.repositories.weather_repository import (
    DefaultWeatherRepository,
)
from forecast.ui.screens.main import MainScreen
from forecast.ui.widgets.daily_forecast import DailyForecastItem


def _sample_payload():
    return {
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
            "apparent_temperature": [26.0 + (h % 5) for h in range(24)],
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


def _service():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=_sample_payload())
    )
    client = OpenMeteoClient(base_url="https://api.open-meteo.com/v1/forecast")
    client._client = httpx.AsyncClient(
        base_url=client.BASE_URL,
        transport=transport,
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": "ForecastCli/1.0"},
    )
    provider = OpenMeteoProvider(client=client)
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)
    return DefaultWeatherService(repo)


@pytest.fixture
def app():
    return ForecastApp(_service())


async def test_app_pushes_main_screen(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, MainScreen)


async def test_weather_hero_renders_temperature(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        digits = app.screen.query_one("#temperature", Digits)
        assert digits.value == "26°C"


async def test_weekly_forecast_populates_table(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.screen.query_one(DataTable)
        assert table.row_count == 1


async def test_daily_forecast_items_populated(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        items = app.screen.query(DailyForecastItem)
        assert len(items) == 24
        # Each item should have a non-default temperature rendered.
        temps = [item.query_one(".temp", Static).content for item in items]
        assert all("°" in str(t) for t in temps)


async def test_toggle_dark_binding(app):
    async with app.run_test() as pilot:
        await pilot.pause()
        initial = app.theme
        await pilot.press("d")
        assert app.theme != initial


async def test_weather_hero_handles_provider_error():
    """The UI must not crash when the provider fails; it should render an error state."""

    def handler(req):
        return httpx.Response(400, json={"error": True, "reason": "bad"})

    transport = httpx.MockTransport(handler)
    client = OpenMeteoClient(base_url="https://api.open-meteo.com/v1/forecast")
    client._client = httpx.AsyncClient(
        base_url=client.BASE_URL,
        transport=transport,
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": "x"},
    )
    provider = OpenMeteoProvider(client=client)
    cache = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    repo = DefaultWeatherRepository(provider=provider, cache=cache)
    service = DefaultWeatherService(repo)

    app = ForecastApp(service)
    async with app.run_test() as pilot:
        await pilot.pause()
        # The app must still be running and the hero must show an error state.
        assert app.screen is not None
        digits = app.screen.query_one("#temperature", Digits)
        assert digits.value == "--°"
        summary = app.screen.query_one("#summary", Static)
        assert "unavailable" in str(summary.content).lower()
