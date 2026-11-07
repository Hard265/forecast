"""Domain model for user preferences."""

from __future__ import annotations

from dataclasses import dataclass

from forecast.domain.models.location import Location


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """Persisted user preferences."""

    primary_location: Location | None = None
    temperature_unit: str = "celsius"
    wind_speed_unit: str = "km/h"
    precipitation_unit: str = "mm"
    use_24_hour_clock: bool = True
