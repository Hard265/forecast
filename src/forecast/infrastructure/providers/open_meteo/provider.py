from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location
from forecast.infrastructure.providers.open_meteo.client import OpenMeteoClient
from forecast.infrastructure.providers.open_meteo.mapper import OpenMeteoMapper


class OpenMeteoProvider:
    def __init__(
        self,
        client: OpenMeteoClient | None = None,
        mapper: OpenMeteoMapper | None = None,
    ) -> None:
        self._client = client or OpenMeteoClient()
        self._mapper = mapper or OpenMeteoMapper()

    async def fetch_current(self, location: Location) -> CurrentWeather:
        response = await self._client.get_weather(
            location.coordinates.latitude,
            location.coordinates.longitude,
        )
        return self._mapper.to_current_weather(response, location)

    async def fetch_forecast(self, location: Location) -> Forecast:
        response = await self._client.get_weather(
            location.coordinates.latitude,
            location.coordinates.longitude,
        )
        return self._mapper.to_forecast(response, location)

    async def fetch_alerts(self, location: Location) -> tuple[WeatherAlert, ...]:
        return ()

    async def fetch_snapshot(
        self, location: Location
    ) -> tuple[CurrentWeather, Forecast, tuple[WeatherAlert, ...]]:
        """Fetch current, forecast, and alerts in a single upstream request."""
        response = await self._client.get_weather(
            location.coordinates.latitude,
            location.coordinates.longitude,
        )
        current = self._mapper.to_current_weather(response, location)
        forecast = self._mapper.to_forecast(response, location)
        alerts = await self.fetch_alerts(location)
        return current, forecast, alerts

    async def close(self) -> None:
        await self._client.close()
