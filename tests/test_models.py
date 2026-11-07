"""Tests for the domain models."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from forecast.domain.models.atmospheric import AtmosphericConditions
from forecast.domain.models.conditions import WeatherCondition, WeatherDescription
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import DailyForecast, Forecast, HourlyForecast
from forecast.domain.models.location import Coordinates, Location
from forecast.domain.models.precipitation import Precipitation
from forecast.domain.models.temperature import Temperature
from forecast.domain.models.wind import Wind


def test_location_is_frozen():
    loc = Location(
        name="X",
        country="Y",
        region=None,
        coordinates=Coordinates(1.0, 2.0),
        timezone="UTC",
    )
    with pytest.raises(FrozenInstanceError):
        loc.name = "Z"  # type: ignore[misc]


def test_temperature_defaults():
    t = Temperature(current=20.0, feels_like=22.0)
    assert t.unit == "celsius"
    assert t.minimum is None
    assert t.maximum is None


def test_wind_defaults():
    w = Wind(speed=5.0, direction=180.0)
    assert w.gust is None
    assert w.unit == "m/s"


def test_weather_condition_values():
    assert WeatherCondition.CLEAR.value == "clear"
    assert WeatherCondition.THUNDERSTORM.value == "thunderstorm"


def test_weather_description_icon_optional():
    d = WeatherDescription(condition=WeatherCondition.CLEAR, description="Clear")
    assert d.icon_code is None
    assert d.is_day is True


def test_hourly_forecast_is_frozen():
    hourly = HourlyForecast(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        temperature=10.0,
        feels_like=10.0,
        condition=WeatherDescription(
            condition=WeatherCondition.CLEAR, description="Clear"
        ),
        precipitation_probability=0.0,
        humidity=50.0,
        wind=Wind(speed=1.0, direction=0.0),
    )
    with pytest.raises(FrozenInstanceError):
        hourly.temperature = 11.0  # type: ignore[misc]


def test_daily_forecast_optional_fields():
    daily = DailyForecast(
        date=datetime(2026, 1, 1, tzinfo=UTC),
        temperature=Temperature(current=10.0, feels_like=10.0),
        condition=WeatherDescription(
            condition=WeatherCondition.CLEAR, description="Clear"
        ),
        precipitation=Precipitation(probability=0.0, amount=0.0),
        wind=Wind(speed=1.0, direction=0.0),
        sunrise=datetime(2026, 1, 1, 6, tzinfo=UTC),
        sunset=datetime(2026, 1, 1, 18, tzinfo=UTC),
    )
    assert daily.uv_index is None
    assert daily.sunrise is not None


def test_forecast_aggregates():
    loc = Location("X", "Y", None, Coordinates(0.0, 0.0), "UTC")
    forecast = Forecast(
        location=loc,
        hourly=(),
        daily=(),
        generated_at=datetime.now(UTC),
    )
    assert forecast.hourly == ()
    assert forecast.daily == ()


def test_current_weather_full_construction():
    loc = Location("X", "Y", None, Coordinates(0.0, 0.0), "UTC")
    cw = CurrentWeather(
        location=loc,
        observed_at=datetime.now(UTC),
        temperature=Temperature(current=20.0, feels_like=21.0),
        conditions=WeatherDescription(
            condition=WeatherCondition.CLEAR, description="Clear"
        ),
        atmospheric=AtmosphericConditions(
            humidity=50.0, pressure=1013.0, visibility=None, cloud_cover=10.0
        ),
        wind=Wind(speed=2.0, direction=90.0),
        precipitation=Precipitation(probability=0.0, amount=0.0),
    )
    assert cw.uv_index is None
    assert cw.atmospheric.pressure == 1013.0
