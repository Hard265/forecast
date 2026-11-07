import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

class MemoryWeatherCache:

    def __init__(self) -> None:
        self._entries: dict[str, tuple[Any, datetime]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._entries.get(key)

            if entry is None:
                return None

            value, expires_at = entry

            if datetime.now(timezone.utc) >= expires_at:
                self._entries.pop(key, None)
                return None

            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("TTL must be positive")

        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=ttl_seconds
        )

        async with self._lock:
            self._entries[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._entries.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._entries.clear()
