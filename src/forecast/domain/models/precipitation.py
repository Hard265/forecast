from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Precipitation:
    probability: float
    amount: float
    rain: float = 0.0
    snow: float = 0.0
    unit: str = "mm"
