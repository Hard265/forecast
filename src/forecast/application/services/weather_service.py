
from forecast.application.repositories.weather_repository import WeatherRepository
from forecast.domain.models.app import WeatherSnapshot
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location


class DefaultWeatherService:
    def __init__(self, repository: WeatherRepository) -> None:
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
        snapshot = await self._repository.get_snapshot(location, force_refresh=refresh)
        return snapshot
