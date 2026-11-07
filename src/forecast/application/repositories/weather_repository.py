from typing import Protocol

from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.app import WeatherSnapshot
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location


class WeatherRepository(Protocol):
    async def get_current(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> CurrentWeather: ...

    async def get_forecast(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> Forecast: ...

    async def get_alerts(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> tuple[WeatherAlert, ...]: ...

    async def get_snapshot(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> WeatherSnapshot: ...
