from dataclasses import dataclass
from datetime import datetime

from forecast.domain.models.atmospheric import AtmosphericConditions
from forecast.domain.models.conditions import WeatherDescription
from forecast.domain.models.location import Location
from forecast.domain.models.precipitation import Precipitation
from forecast.domain.models.temperature import Temperature
from forecast.domain.models.wind import Wind


@dataclass(frozen=True, slots=True)
class CurrentWeather:
    location: Location
    observed_at: datetime
    temperature: Temperature
    conditions: WeatherDescription
    atmospheric: AtmosphericConditions
    wind: Wind
    precipitation: Precipitation
    uv_index: float | None = None
