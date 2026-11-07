from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Wind:
    speed: float
    direction: float
    gust: float | None = None
    unit: str = "m/s"
