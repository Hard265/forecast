import httpx

from forecast.domain.errors import WeatherProviderError
from forecast.infrastructure.providers.open_meteo.dto import OpenMeteoResponseDTO


class OpenMeteoClient:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    CURRENT_PARAMS = (
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "is_day",
        "precipitation",
        "rain",
        "showers",
        "snowfall",
        "weather_code",
        "cloud_cover",
        "pressure_msl",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
    )
    HOURLY_PARAMS = (
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "precipitation_probability",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
        "wind_direction_10m",
    )
    DAILY_PARAMS = (
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "sunrise",
        "sunset",
        "uv_index_max",
        "precipitation_sum",
        "precipitation_probability_max",
        "wind_speed_10m_max",
        "wind_direction_10m_dominant",
    )

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = 10.0,
        connect_timeout: float = 5.0,
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
    ) -> None:
        self._base_url = base_url or self.BASE_URL
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout, connect=connect_timeout),
            headers={"User-Agent": "ForecastCli/1.0"},
        )
        self._max_retries = max(0, max_retries)
        self._backoff_seconds = max(0.0, backoff_seconds)

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> OpenMeteoResponseDTO:
        """Fetch weather for a location with retry/backoff on transient errors."""
        import asyncio

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.get(
                    "",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": ",".join(self.CURRENT_PARAMS),
                        "hourly": ",".join(self.HOURLY_PARAMS),
                        "daily": ",".join(self.DAILY_PARAMS),
                        "timezone": "auto",
                        "forecast_days": 7,
                    },
                )
                response.raise_for_status()
                return OpenMeteoResponseDTO.model_validate(response.json())
            except httpx.HTTPStatusError as exc:
                # Only retry on 5xx and 429; 4xx are permanent failures.
                if exc.response.status_code >= 500 or exc.response.status_code == 429:
                    last_error = exc
                else:
                    raise WeatherProviderError(
                        f"Open-Meteo rejected request: {exc.response.status_code}"
                    ) from exc
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc

            if attempt < self._max_retries:
                await asyncio.sleep(self._backoff_seconds * (2**attempt))

        raise WeatherProviderError(
            f"Open-Meteo request failed after {self._max_retries + 1} attempts"
        ) from last_error

    async def close(self) -> None:
        await self._client.aclose()
