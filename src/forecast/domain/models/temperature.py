from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Temperature:
    current: float
    feels_like: float
    minimum: float | None = None
    maximum: float | None = None
    unit: str = "celsius"
