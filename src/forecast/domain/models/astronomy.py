from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SunTimes:
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime | None = None


@dataclass(frozen=True, slots=True)
class MoonInformation:
    phase: str
    illumination: float
    moonrise: datetime | None
    moonset: datetime | None
