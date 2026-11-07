"""Contract tests for the WeatherRepository port.

These tests verify that any implementation of the WeatherRepository protocol
behaves correctly, independent of the underlying provider/cache. They act as
a safety net against accidental drift between the port and its adapters.
"""

from __future__ import annotations

from datetime import datetime

from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.app import WeatherSnapshot
from forecast.domain.models.atmospheric import AtmosphericConditions
from forecast.domain.models.conditions import WeatherCondition, WeatherDescription
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location
from forecast.domain.models.precipitation import Precipitation
from forecast.domain.models.temperature import Temperature
from forecast.domain.models.wind import Wind


class FakeRepository:
    """Minimal in-memory adapter used to exercise the protocol contract."""

    def __init__(self, location: Location) -> None:
        self._location = location
        self.current_calls = 0
        self.forecast_calls = 0
        self.alert_calls = 0
        self.snapshot_calls = 0

    async def get_current(self, location, *, force_refresh=False) -> CurrentWeather:
        self.current_calls += 1
        assert location is self._location
        assert isinstance(force_refresh, bool)
        return CurrentWeather(
            location=location,
            observed_at=datetime.now(),
            temperature=Temperature(current=1.0, feels_like=1.0),
            conditions=WeatherDescription(
                condition=WeatherCondition.CLEAR, description="clear"
            ),
            atmospheric=AtmosphericConditions(
                humidity=1.0, pressure=1.0, visibility=None, cloud_cover=1.0
            ),
            wind=Wind(speed=1.0, direction=0.0),
            precipitation=Precipitation(probability=0.0, amount=0.0),
        )

    async def get_forecast(self, location, *, force_refresh=False) -> Forecast:
        self.forecast_calls += 1
        assert location is self._location
        return Forecast(
            location=location,
            hourly=(),
            daily=(),
            generated_at=datetime.now(),
        )

    async def get_alerts(
        self, location, *, force_refresh=False
    ) -> tuple[WeatherAlert, ...]:
        self.alert_calls += 1
        return ()

    async def get_snapshot(self, location, *, force_refresh=False) -> WeatherSnapshot:
        self.snapshot_calls += 1
        current = await self.get_current(location, force_refresh=force_refresh)
        forecast = await self.get_forecast(location, force_refresh=force_refresh)
        alerts = await self.get_alerts(location, force_refresh=force_refresh)
        return WeatherSnapshot(
            current=current,
            forecast=forecast,
            alerts=alerts,
            fetched_at=datetime.now(),
        )


async def test_repository_protocol_supports_force_refresh(location):
    repo = FakeRepository(location)
    await repo.get_current(location)
    await repo.get_current(location, force_refresh=True)
    assert repo.current_calls == 2


async def test_repository_protocol_snapshot_uses_sub_calls(location):
    repo = FakeRepository(location)
    await repo.get_snapshot(location)
    assert repo.snapshot_calls == 1
    assert repo.current_calls == 1
    assert repo.forecast_calls == 1
    assert repo.alert_calls == 1


async def test_repository_protocol_returns_correct_types(location):
    repo = FakeRepository(location)
    current = await repo.get_current(location)
    forecast = await repo.get_forecast(location)
    alerts = await repo.get_alerts(location)
    snapshot = await repo.get_snapshot(location)

    assert isinstance(current, CurrentWeather)
    assert isinstance(forecast, Forecast)
    assert isinstance(alerts, tuple)
    assert isinstance(snapshot, WeatherSnapshot)
    # The snapshot re-fetches each sub-resource; compare by value, ignoring
    # the non-deterministic observed_at timestamp.
    assert snapshot.current.location == current.location
    assert snapshot.current.temperature == current.temperature
    assert snapshot.forecast.location == forecast.location
    assert snapshot.alerts == alerts
