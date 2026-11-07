from typing import Any

import httpx

class OpenMeteoClient:

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(10.0, connect=5.0),
            headers={
                "User-Agent": "ForecastCli/1.0",
            },
        )

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[Any, Any]:

        response = await self._client.get(
            "",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "is_day,"
                    "precipitation,"
                    "rain,"
                    "showers,"
                    "snowfall,"
                    "weather_code,"
                    "cloud_cover,"
                    "pressure_msl,"
                    "wind_speed_10m,"
                    "wind_direction_10m,"
                    "wind_gusts_10m"
                ),
                "hourly": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "precipitation_probability,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "sunrise,"
                    "sunset,"
                    "uv_index_max,"
                    "precipitation_sum,"
                    "precipitation_probability_max"
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
        )

        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
