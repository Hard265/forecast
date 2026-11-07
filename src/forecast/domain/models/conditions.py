from dataclasses import dataclass
from enum import Enum


class WeatherCondition(Enum):
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    THUNDERSTORM = "thunderstorm"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class WeatherDescription:
    condition: WeatherCondition
    description: str
    icon_code: str | None = None
    is_day: bool = True
