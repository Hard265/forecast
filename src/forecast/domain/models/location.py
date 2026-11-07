from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class Location:
    name: str
    country: str
    region: str | None
    coordinates: Coordinates
    timezone: str
