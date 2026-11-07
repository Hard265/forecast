from datetime import datetime

from forecast.application.providers.weather_provider import WeatherProvider
from forecast.application.repositories.weather_cache import WeatherCache
from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.app import WeatherSnapshot
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location

def _now():
    return datetime.now()

class DefaultWeatherRepository:
    def __init__(
        self,
        provider: WeatherProvider,
        cache: WeatherCache,
    ):
        self._provider = provider
        self._cache = cache

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
                return cached.data

        weather = await self._provider.fetch_current(location)

        await self._cache.set(
            key,
            weather,
            ttl_seconds=600,
        )

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
                return cached.data

        forecast = await self._provider.fetch_forecast(location)

        await self._cache.set(
            key,
            forecast,
            ttl_seconds=1800,
        )

        return forecast

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

    async def get_alerts(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> tuple[WeatherAlert,...]:
        return await self._provider.fetch_alerts(location)

    async def get_snapshot(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> WeatherSnapshot:
        snapshot = WeatherSnapshot(
            alerts= await self.get_alerts(location),
            fetched_at = _now(),
          current= await self.get_current(location),
            forecast= await self.get_forecast(location)
        )
        return snapshot
