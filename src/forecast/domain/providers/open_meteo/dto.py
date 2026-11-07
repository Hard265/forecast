from pydantic import BaseModel, ConfigDict

class OpenMeteoCurrentDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: str
    temperature_2m: float
    apparent_temperature: float
    relative_humidity_2m: float
    weather_code: int
    is_day: int
    precipitation: float
    cloud_cover: float
    pressure_msl: float
    wind_speed_10m: float
    wind_direction_10m: float
    wind_gusts_10m: float | None = None


class OpenMeteoResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float
    longitude: float
    timezone: str
    current: OpenMeteoCurrentDTO
