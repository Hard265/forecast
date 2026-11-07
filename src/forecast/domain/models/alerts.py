from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class AlertSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


@dataclass(frozen=True, slots=True)
class WeatherAlert:
    id: str
    title: str
    description: str
    severity: AlertSeverity
    starts_at: datetime
    ends_at: datetime
    source: str
    affected_areas: tuple[str, ...]
