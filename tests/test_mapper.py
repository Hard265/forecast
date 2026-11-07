"""Tests for the Open-Meteo DTO and mapper."""

from zoneinfo import ZoneInfo

from forecast.domain.models.conditions import WeatherCondition
from forecast.domain.models.location import Coordinates, Location
from forecast.infrastructure.providers.open_meteo.dto import (
    OpenMeteoCurrentDTO,
    OpenMeteoResponseDTO,
)
from forecast.infrastructure.providers.open_meteo.mapper import OpenMeteoMapper


def _location() -> Location:
    return Location(
        name="Blantyre",
        country="Malawi",
        region="Southern",
        coordinates=Coordinates(latitude=-15.78, longitude=35.0),
        timezone="Africa/Blantyre",
    )


def test_dto_ignores_unknown_fields():
    dto = OpenMeteoCurrentDTO(
        time="2026-01-01T00:00",
        temperature_2m=1.0,
        apparent_temperature=1.0,
        relative_humidity_2m=1.0,
        weather_code=0,
        is_day=1,
        precipitation=0.0,
        cloud_cover=0.0,
        pressure_msl=1000.0,
        wind_speed_10m=1.0,
        wind_direction_10m=1.0,
        wind_gusts_10m=1.0,
        future_field="ignored",
    )
    assert dto.temperature_2m == 1.0


def test_mapper_current_weather(sample_payload, location):
    dto = OpenMeteoResponseDTO.model_validate(sample_payload)
    mapper = OpenMeteoMapper()
    current = mapper.to_current_weather(dto, location)

    assert current.location is location
    assert current.temperature.current == 26.0
    assert current.temperature.feels_like == 27.0
    assert current.conditions.condition == WeatherCondition.PARTLY_CLOUDY
    assert current.conditions.is_day is True
    assert current.wind.speed == 5.0
    assert current.wind.unit == "km/h"
    assert current.atmospheric.pressure == 1010.0
    assert current.precipitation.amount == 0.0
    assert current.observed_at.tzinfo == ZoneInfo("Africa/Blantyre")


def test_mapper_unknown_weather_code(sample_payload, location):
    payload = {
        "latitude": -15.78,
        "longitude": 35.0,
        "timezone": "Africa/Blantyre",
        "current": {
            "time": "2026-01-01T00:00",
            "temperature_2m": 1.0,
            "apparent_temperature": 1.0,
            "relative_humidity_2m": 1.0,
            "weather_code": 9999,
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
            "weather_code": [9999],
            "wind_speed_10m": [1.0],
            "wind_direction_10m": [1.0],
        },
        "daily": {
            "time": ["2026-01-01"],
            "weather_code": [9999],
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
    dto = OpenMeteoResponseDTO.model_validate(payload)
    current = OpenMeteoMapper().to_current_weather(dto, _location())
    assert current.conditions.condition == WeatherCondition.UNKNOWN


def test_mapper_to_forecast(sample_payload, location):
    dto = OpenMeteoResponseDTO.model_validate(sample_payload)
    forecast = OpenMeteoMapper().to_forecast(dto, location)

    assert forecast.location is location
    assert len(forecast.hourly) == 24
    assert len(forecast.daily) == 1

    first_hourly = forecast.hourly[0]
    assert first_hourly.temperature == 26.0
    assert first_hourly.precipitation_probability == 0.1
    assert first_hourly.humidity == 60.0
    assert first_hourly.timestamp.tzinfo == ZoneInfo("Africa/Blantyre")

    daily = forecast.daily[0]
    assert daily.temperature.minimum == 20.0
    assert daily.temperature.maximum == 28.0
    assert daily.uv_index == 6.0
    assert daily.precipitation.probability == 0.2
    assert daily.precipitation.amount == 0.0
    assert daily.sunrise.tzinfo == ZoneInfo("Africa/Blantyre")
    assert daily.sunset.tzinfo == ZoneInfo("Africa/Blantyre")
    assert forecast.generated_at.tzinfo == ZoneInfo("Africa/Blantyre")
