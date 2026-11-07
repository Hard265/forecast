import asyncio
from datetime import datetime, timezone

from forecast.domain.models.app import WeatherSnapshot
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location
from forecast.domain.models.current_weather import CurrentWeather
from forecast.application.repositories.weather_repository import WeatherRepository

class DefaultWeatherService:
    def __init__(
        self,
        repository: WeatherRepository,
    ):
        self._repository = repository

    async def get_current_weather(
        self,
        location: Location,
        *,
        refresh: bool = False,
    ) -> CurrentWeather:

        return await self._repository.get_current(
            location,
            force_refresh=refresh,
        )

    async def get_forecast(
        self,
        location: Location,
        *,
        refresh: bool = False,
    ) -> Forecast:

        return await self._repository.get_forecast(
            location,
            force_refresh=refresh,
        )

    async def get_weather_dashboard(
        self,
        location: Location,
        *,
        refresh: bool = False,
    ) -> WeatherSnapshot:

        current, forecast, alerts = await asyncio.gather(
            self._repository.get_current(
                location,
                force_refresh=refresh,
            ),
            self._repository.get_forecast(
                location,
                force_refresh=refresh,
            ),
            self._repository.get_alerts(
                location,
                force_refresh=refresh,
            ),
        )

        return WeatherSnapshot(
            current=current,
            forecast=forecast,
            alerts=alerts,
            fetched_at=datetime.now(timezone.utc),
        )
