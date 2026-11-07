from typing import Protocol

from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location


class WeatherProvider(Protocol):
    async def fetch_current(self, location: Location) -> CurrentWeather: ...

    async def fetch_forecast(self, location: Location) -> Forecast: ...

    async def fetch_alerts(self, location: Location) -> tuple[WeatherAlert, ...]: ...
