from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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
