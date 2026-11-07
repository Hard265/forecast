import asyncio
from datetime import datetime

from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.app import WeatherSnapshot
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location
from forecast.infrastructure.cache.tiered import TieredWeatherCache
from forecast.infrastructure.providers.open_meteo.provider import OpenMeteoProvider


def _now() -> datetime:
    return datetime.now()


class DefaultWeatherRepository:
    CURRENT_TTL_SECONDS = 600
    FORECAST_TTL_SECONDS = 1800

    def __init__(
        self,
        provider: OpenMeteoProvider,
        cache: TieredWeatherCache[object],
        *,
        current_ttl_seconds: int = CURRENT_TTL_SECONDS,
        forecast_ttl_seconds: int = FORECAST_TTL_SECONDS,
    ) -> None:
        self._provider = provider
        self._cache = cache
        if current_ttl_seconds <= 0:
            raise ValueError("current_ttl_seconds must be positive")
        if forecast_ttl_seconds <= 0:
            raise ValueError("forecast_ttl_seconds must be positive")
        self._current_ttl = current_ttl_seconds
        self._forecast_ttl = forecast_ttl_seconds

    async def get_current(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> CurrentWeather:
        key = self._current_cache_key(location)

        if not force_refresh:
            cached = await self._cache.get(key)
            if cached is not None and not cached.is_expired:
                return cached.data  # type: ignore[no-any-return]

        weather = await self._provider.fetch_current(location)
        await self._cache.set(key, weather, self._current_ttl)
        return weather

    async def get_forecast(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> Forecast:
        key = self._forecast_cache_key(location)

        if not force_refresh:
            cached = await self._cache.get(key)
            if cached is not None and not cached.is_expired:
                return cached.data  # type: ignore[no-any-return]

        forecast = await self._provider.fetch_forecast(location)
        await self._cache.set(key, forecast, self._forecast_ttl)
        return forecast

    async def get_alerts(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> tuple[WeatherAlert, ...]:
        return await self._provider.fetch_alerts(location)

    async def get_snapshot(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> WeatherSnapshot:
        current, forecast, alerts = await asyncio.gather(
            self.get_current(location, force_refresh=force_refresh),
            self.get_forecast(location, force_refresh=force_refresh),
            self.get_alerts(location, force_refresh=force_refresh),
        )
        return WeatherSnapshot(
            current=current,
            forecast=forecast,
            alerts=alerts,
            fetched_at=_now(),
        )

    def _current_cache_key(self, location: Location) -> str:
        return (
            f"weather:current:"
            f"{location.coordinates.latitude}:"
            f"{location.coordinates.longitude}"
        )

    def _forecast_cache_key(self, location: Location) -> str:
        return (
            f"weather:forecast:"
            f"{location.coordinates.latitude}:"
            f"{location.coordinates.longitude}"
        )
