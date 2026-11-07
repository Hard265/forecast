from dataclasses import dataclass
from datetime import datetime

from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location


@dataclass(frozen=True, slots=True)
class WeatherPreferences:
    temperature_unit: str = "celsius"
    wind_speed_unit: str = "m/s"
    precipitation_unit: str = "mm"
    use_24_hour_clock: bool = True


@dataclass(frozen=True, slots=True)
class SavedLocation:
    id: str
    location: Location
    is_primary: bool = False


@dataclass(frozen=True, slots=True)
class WeatherSnapshot:
    current: CurrentWeather
    forecast: Forecast
    alerts: tuple[WeatherAlert, ...]
    fetched_at: datetime
