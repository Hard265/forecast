"""In-memory cache implementation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from forecast.domain.models.cache import CacheEntry


class MemoryWeatherCache[T]:
    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry[T]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> CacheEntry[T] | None:
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.is_expired:
                self._entries.pop(key, None)
                return None
            return entry

    async def set(self, key: str, value: T, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("TTL must be positive")
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        async with self._lock:
            self._entries[key] = CacheEntry(
                data=value,
                fetched_at=datetime.now(UTC),
                expires_at=expires_at,
            )

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._entries.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._entries.clear()
