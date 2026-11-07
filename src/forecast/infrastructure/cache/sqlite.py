"""SQLite-backed cache implementation."""

from __future__ import annotations

import asyncio
import pickle
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

from forecast.domain.models.cache import CacheEntry


class SQLiteWeatherCache[T]:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        async with self._lock:
            if self._initialized:
                return

            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(self._database_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS weather_cache (
                        cache_key TEXT PRIMARY KEY,
                        payload BLOB NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    )
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS
                    idx_weather_cache_expiry
                    ON weather_cache(expires_at)
                """)
                await db.commit()
            self._initialized = True

    async def get(self, key: str) -> CacheEntry[T] | None:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            async with db.execute(
                "SELECT payload, created_at, expires_at FROM weather_cache WHERE cache_key = ?",
                (key,),
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return None

            payload, created_at, expires_at = row
            expiry = datetime.fromisoformat(expires_at)

            if datetime.now(UTC) >= expiry:
                await db.execute(
                    "DELETE FROM weather_cache WHERE cache_key = ?",
                    (key,),
                )
                await db.commit()
                return None

            return CacheEntry(
                data=pickle.loads(payload),
                fetched_at=datetime.fromisoformat(created_at),
                expires_at=expiry,
            )

    async def set(self, key: str, value: T, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("TTL must be positive")

        await self.initialize()
        now = datetime.now(UTC)
        expires = now + timedelta(seconds=ttl_seconds)

        async with aiosqlite.connect(self._database_path) as db:
            await db.execute(
                """
                INSERT INTO weather_cache (
                    cache_key, payload, created_at, expires_at
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
            """,
                (
                    key,
                    pickle.dumps(value),
                    now.isoformat(),
                    expires.isoformat(),
                ),
            )
            await db.commit()

    async def delete(self, key: str) -> None:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute(
                "DELETE FROM weather_cache WHERE cache_key = ?",
                (key,),
            )
            await db.commit()

    async def clear(self) -> None:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("DELETE FROM weather_cache")
            await db.commit()
