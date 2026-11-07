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


class OpenMeteoHourlyDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: list[str]
    temperature_2m: list[float]
    relative_humidity_2m: list[float]
    precipitation_probability: list[float]
    precipitation: list[float]
    weather_code: list[int]
    wind_speed_10m: list[float]
    wind_direction_10m: list[float]


class OpenMeteoDailyDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time: list[str]
    weather_code: list[int]
    temperature_2m_max: list[float]
    temperature_2m_min: list[float]
    sunrise: list[str]
    sunset: list[str]
    uv_index_max: list[float]
    precipitation_sum: list[float]
    precipitation_probability_max: list[float]
    wind_speed_10m: list[float]
    wind_direction_10m: list[float]


class OpenMeteoResponseDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float
    longitude: float
    timezone: str
    current: OpenMeteoCurrentDTO
    hourly: OpenMeteoHourlyDTO
    daily: OpenMeteoDailyDTO
