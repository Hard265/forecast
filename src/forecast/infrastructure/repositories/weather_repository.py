import asyncio
from datetime import UTC, datetime

from forecast.domain.models.alerts import WeatherAlert
from forecast.domain.models.app import WeatherSnapshot
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import Forecast
from forecast.domain.models.location import Location
from forecast.infrastructure.cache.tiered import TieredWeatherCache
from forecast.infrastructure.providers.open_meteo.provider import OpenMeteoProvider


def _now() -> datetime:
    return datetime.now(UTC)


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
        self._inflight: dict[str, asyncio.Task[tuple[CurrentWeather, Forecast, tuple[WeatherAlert, ...]]]] = {}
        self._lock = asyncio.Lock()

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
        current, forecast, _alerts = await self._fetch_snapshot(location, force_refresh=force_refresh)
        await self._cache.set(key, current, self._current_ttl)
        await self._cache.set(self._forecast_cache_key(location), forecast, self._forecast_ttl)
        return current

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
        current, forecast, _alerts = await self._fetch_snapshot(location, force_refresh=force_refresh)
        await self._cache.set(self._current_cache_key(location), current, self._current_ttl)
        await self._cache.set(key, forecast, self._forecast_ttl)
        return forecast

    async def get_alerts(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> tuple[WeatherAlert, ...]:
        # Open-Meteo exposes no alert endpoint in this client; alerts are empty.
        return ()

    async def get_snapshot(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> WeatherSnapshot:
        current_key = self._current_cache_key(location)
        forecast_key = self._forecast_cache_key(location)

        cached_current = None
        cached_forecast = None
        if not force_refresh:
            cc = await self._cache.get(current_key)
            if cc is not None and not cc.is_expired:
                cached_current = cc.data
            cf = await self._cache.get(forecast_key)
            if cf is not None and not cf.is_expired:
                cached_forecast = cf.data

        if cached_current is not None and cached_forecast is not None:
            return WeatherSnapshot(
                current=cached_current,  # type: ignore[arg-type]
                forecast=cached_forecast,  # type: ignore[arg-type]
                alerts=(),
                fetched_at=_now(),
            )

        current, forecast, alerts = await self._fetch_snapshot(location, force_refresh=force_refresh)
        await self._cache.set(current_key, current, self._current_ttl)
        await self._cache.set(forecast_key, forecast, self._forecast_ttl)
        return WeatherSnapshot(
            current=current,
            forecast=forecast,
            alerts=alerts,
            fetched_at=_now(),
        )

    async def _fetch_snapshot(
        self,
        location: Location,
        *,
        force_refresh: bool = False,
    ) -> tuple[CurrentWeather, Forecast, tuple[WeatherAlert, ...]]:
        inflight_key = f"{location.coordinates.latitude}:{location.coordinates.longitude}:{int(force_refresh)}"
        async with self._lock:
            task = self._inflight.get(inflight_key)
            if task is None or task.done():
                task = asyncio.create_task(
                    self._provider.fetch_snapshot(location)
                )
                self._inflight[inflight_key] = task
        try:
            return await task
        finally:
            async with self._lock:
                if self._inflight.get(inflight_key) is task:
                    del self._inflight[inflight_key]

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
