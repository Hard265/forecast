"""Read-through tiered cache: fast in-memory layer with persistent fallback."""

from __future__ import annotations

from datetime import UTC, datetime

from forecast.domain.models.cache import CacheEntry


class TieredWeatherCache[T]:
    """Read-through cache: fast in-memory layer with persistent SQLite fallback."""

    def __init__(self, memory, persistent) -> None:
        self._memory = memory
        self._persistent = persistent

    async def get(self, key: str) -> CacheEntry[T] | None:
        entry = await self._memory.get(key)
        if entry is not None:
            return entry

        entry = await self._persistent.get(key)
        if entry is None:
            return None

        # Read-through: repopulate the fast layer so subsequent reads are O(1).
        remaining = int((entry.expires_at - datetime.now(UTC)).total_seconds())
        if remaining > 0:
            await self._memory.set(key, entry.data, remaining)
        return entry

    async def set(self, key: str, value: T, ttl_seconds: int) -> None:
        await self._memory.set(key, value, ttl_seconds)
        await self._persistent.set(key, value, ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._memory.delete(key)
        await self._persistent.delete(key)

    async def clear(self) -> None:
        await self._memory.clear()
        await self._persistent.clear()
