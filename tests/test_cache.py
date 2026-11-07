"""Tests for the cache implementations."""

from datetime import UTC, datetime, timedelta

import pytest

from forecast.domain.models.cache import CacheEntry
from forecast.infrastructure.cache.memory import MemoryWeatherCache
from forecast.infrastructure.cache.sqlite import SQLiteWeatherCache
from forecast.infrastructure.cache.tiered import TieredWeatherCache


async def test_memory_cache_round_trip():
    cache = MemoryWeatherCache()
    await cache.set("k", "v", ttl_seconds=60)
    entry = await cache.get("k")
    assert isinstance(entry, CacheEntry)
    assert entry.data == "v"
    assert not entry.is_expired


async def test_memory_cache_miss():
    cache = MemoryWeatherCache()
    assert await cache.get("missing") is None


async def test_memory_cache_expired_entry_is_removed():
    cache = MemoryWeatherCache()
    await cache.set("k", "v", ttl_seconds=60)
    # Force expiry by injecting an expired entry directly.
    cache._entries["k"] = CacheEntry(
        data="v",
        fetched_at=datetime.now(UTC) - timedelta(seconds=120),
        expires_at=datetime.now(UTC) - timedelta(seconds=60),
    )
    assert await cache.get("k") is None
    assert "k" not in cache._entries


async def test_memory_cache_negative_ttl_rejected():
    cache = MemoryWeatherCache()
    with pytest.raises(ValueError):
        await cache.set("k", "v", ttl_seconds=0)
    with pytest.raises(ValueError):
        await cache.set("k", "v", ttl_seconds=-5)


async def test_memory_cache_delete_and_clear():
    cache = MemoryWeatherCache()
    await cache.set("a", 1, ttl_seconds=60)
    await cache.set("b", 2, ttl_seconds=60)
    await cache.delete("a")
    assert await cache.get("a") is None
    assert (await cache.get("b")).data == 2
    await cache.clear()
    assert await cache.get("b") is None


async def test_sqlite_cache_round_trip(tmp_path):
    cache = SQLiteWeatherCache(database_path=str(tmp_path / "w.db"))
    await cache.set("k", {"x": 1}, ttl_seconds=60)
    entry = await cache.get("k")
    assert entry is not None
    assert entry.data == {"x": 1}
    assert not entry.is_expired


async def test_sqlite_cache_miss(tmp_path):
    cache = SQLiteWeatherCache(database_path=str(tmp_path / "w.db"))
    assert await cache.get("missing") is None


async def test_sqlite_cache_overwrite(tmp_path):
    cache = SQLiteWeatherCache(database_path=str(tmp_path / "w.db"))
    await cache.set("k", "v1", ttl_seconds=60)
    await cache.set("k", "v2", ttl_seconds=60)
    assert (await cache.get("k")).data == "v2"


async def test_sqlite_cache_negative_ttl_rejected(tmp_path):
    cache = SQLiteWeatherCache(database_path=str(tmp_path / "w.db"))
    with pytest.raises(ValueError):
        await cache.set("k", "v", ttl_seconds=-1)


async def test_sqlite_cache_delete_and_clear(tmp_path):
    cache = SQLiteWeatherCache(database_path=str(tmp_path / "w.db"))
    await cache.set("a", 1, ttl_seconds=60)
    await cache.set("b", 2, ttl_seconds=60)
    await cache.delete("a")
    assert await cache.get("a") is None
    assert (await cache.get("b")).data == 2
    await cache.clear()
    assert await cache.get("b") is None


async def test_tiered_cache_reads_from_memory_first():
    memory = MemoryWeatherCache()
    persistent = MemoryWeatherCache()
    tiered = TieredWeatherCache(memory=memory, persistent=persistent)

    await memory.set("k", "mem", ttl_seconds=60)
    await persistent.set("k", "persist", ttl_seconds=60)

    entry = await tiered.get("k")
    assert entry.data == "mem"


async def test_tiered_cache_falls_back_to_persistent():
    memory = MemoryWeatherCache()
    persistent = MemoryWeatherCache()
    tiered = TieredWeatherCache(memory=memory, persistent=persistent)

    await persistent.set("k", "persist", ttl_seconds=60)
    entry = await tiered.get("k")
    assert entry.data == "persist"
    # Memory should be populated on read-through miss.
    assert (await memory.get("k")).data == "persist"


async def test_tiered_cache_miss_when_both_empty():
    tiered = TieredWeatherCache(
        memory=MemoryWeatherCache(),
        persistent=MemoryWeatherCache(),
    )
    assert await tiered.get("missing") is None


async def test_tiered_cache_set_writes_both_layers():
    memory = MemoryWeatherCache()
    persistent = MemoryWeatherCache()
    tiered = TieredWeatherCache(memory=memory, persistent=persistent)

    await tiered.set("k", "v", ttl_seconds=60)
    assert (await memory.get("k")).data == "v"
    assert (await persistent.get("k")).data == "v"


async def test_tiered_cache_delete_wipes_both_layers():
    memory = MemoryWeatherCache()
    persistent = MemoryWeatherCache()
    tiered = TieredWeatherCache(memory=memory, persistent=persistent)

    await memory.set("k", "v", ttl_seconds=60)
    await persistent.set("k", "v", ttl_seconds=60)
    await tiered.delete("k")
    assert await memory.get("k") is None
    assert await persistent.get("k") is None


async def test_tiered_cache_clear_wipes_both_layers():
    memory = MemoryWeatherCache()
    persistent = MemoryWeatherCache()
    tiered = TieredWeatherCache(memory=memory, persistent=persistent)

    await memory.set("k", "v", ttl_seconds=60)
    await persistent.set("k", "v", ttl_seconds=60)
    await tiered.clear()
    assert await memory.get("k") is None
    assert await persistent.get("k") is None
