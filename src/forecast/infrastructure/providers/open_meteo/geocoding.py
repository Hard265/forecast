"""Open-Meteo Geocoding API client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from forecast.domain.errors import WeatherProviderError


@dataclass(frozen=True, slots=True)
class GeocodingResultDTO:
    name: str
    country: str | None
    admin1: str | None
    latitude: float
    longitude: float
    timezone: str | None


@dataclass(frozen=True, slots=True)
class GeocodingResponseDTO:
    results: tuple[GeocodingResultDTO, ...] = ()


class GeocodingClient:
    BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float = 10.0,
        connect_timeout: float = 5.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.3,
    ) -> None:
        self._base_url = base_url or self.BASE_URL
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout, connect=connect_timeout),
            headers={"User-Agent": "ForecastCli/1.0"},
        )
        self._max_retries = max(0, max_retries)
        self._backoff_seconds = max(0.0, backoff_seconds)

    async def search(
        self,
        query: str,
        *,
        count: int = 10,
        language: str = "en",
    ) -> tuple[GeocodingResultDTO, ...]:
        if not query.strip():
            return ()

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.get(
                    "",
                    params={
                        "name": query.strip(),
                        "count": count,
                        "language": language,
                        "format": "json",
                    },
                )
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("results", []) or []:
                    results.append(
                        GeocodingResultDTO(
                            name=item.get("name") or "",
                            country=item.get("country"),
                            admin1=item.get("admin1"),
                            latitude=float(item["latitude"]),
                            longitude=float(item["longitude"]),
                            timezone=item.get("timezone"),
                        )
                    )
                return tuple(results)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 or exc.response.status_code == 429:
                    last_error = exc
                else:
                    raise WeatherProviderError(
                        f"Geocoding rejected request: {exc.response.status_code}"
                    ) from exc
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc

            if attempt < self._max_retries:
                await asyncio.sleep(self._backoff_seconds * (2**attempt))

        raise WeatherProviderError(
            f"Geocoding request failed after {self._max_retries + 1} attempts"
        ) from last_error

    async def close(self) -> None:
        await self._client.aclose()
