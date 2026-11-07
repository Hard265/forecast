from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AtmosphericConditions:
    humidity: float
    pressure: float
    visibility: float | None
    cloud_cover: float
