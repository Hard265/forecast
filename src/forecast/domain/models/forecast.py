from dataclasses import dataclass
from datetime import datetime

from forecast.domain.models.conditions import WeatherDescription
from forecast.domain.models.location import Location
from forecast.domain.models.precipitation import Precipitation
from forecast.domain.models.temperature import Temperature
from forecast.domain.models.wind import Wind


@dataclass(frozen=True, slots=True)
class HourlyForecast:
    timestamp: datetime
    temperature: float
    feels_like: float
    condition: WeatherDescription
    precipitation_probability: float
    humidity: float
    wind: Wind


@dataclass(frozen=True, slots=True)
class DailyForecast:
    date: datetime
    temperature: Temperature
    condition: WeatherDescription
    precipitation: Precipitation
    wind: Wind
    sunrise: datetime | None
    sunset: datetime | None
    uv_index: float | None = None


@dataclass(frozen=True, slots=True)
class Forecast:
    location: Location
    hourly: tuple[HourlyForecast, ...]
    daily: tuple[DailyForecast, ...]
    generated_at: datetime
