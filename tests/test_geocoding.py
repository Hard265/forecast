"""Tests for geocoding client with mocked transport."""

from __future__ import annotations

import httpx
import pytest

from forecast.infrastructure.providers.open_meteo.geocoding import GeocodingClient


@pytest.mark.asyncio
async def test_geocoding_search_mocked() -> None:
    payload = {
        "results": [
            {
                "name": "Paris",
                "country": "France",
                "admin1": "Île-de-France",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "timezone": "Europe/Paris",
            },
            {
                "name": "Paris",
                "country": "United States",
                "admin1": "Texas",
                "latitude": 33.6609,
                "longitude": -95.5555,
                "timezone": "America/Chicago",
            },
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = GeocodingClient(base_url="https://geocoding-api.open-meteo.com/v1/search")
    client._client = httpx.AsyncClient(
        base_url=client._base_url,
        transport=transport,
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": "ForecastCli/1.0"},
    )
    results = await client.search("Paris")
    assert len(results) == 2
    assert results[0].name == "Paris"
    assert results[0].country == "France"
    await client.close()
