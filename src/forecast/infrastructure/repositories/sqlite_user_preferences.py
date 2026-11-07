"""SQLite-backed implementation of user preferences repository."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from forecast.application.repositories.user_preferences import UserPreferencesRepository
from forecast.domain.models.location import Coordinates, Location
from forecast.domain.models.preferences import UserPreferences


class SqliteUserPreferencesRepository(UserPreferencesRepository):
    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)

    async def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_locations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    region TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    timezone TEXT NOT NULL,
                    is_primary INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    primary_location_id TEXT,
                    FOREIGN KEY (primary_location_id) REFERENCES saved_locations(id)
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS opened_location_tabs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    region TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    timezone TEXT NOT NULL,
                    position INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            await db.commit()

    async def get_preferences(self) -> UserPreferences:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT primary_location_id FROM user_preferences WHERE id = 1"
            ) as cur:
                pref_row = await cur.fetchone()
            if not pref_row or not pref_row["primary_location_id"]:
                return UserPreferences(primary_location=None)
            primary_id = pref_row["primary_location_id"]
            async with db.execute(
                "SELECT * FROM saved_locations WHERE id = ?",
                (primary_id,),
            ) as cur:
                loc_row = await cur.fetchone()
            if not loc_row:
                return UserPreferences(primary_location=None)
            location = Location(
                name=loc_row["name"],
                country=loc_row["country"],
                region=loc_row["region"],
                coordinates=Coordinates(
                    latitude=float(loc_row["latitude"]),
                    longitude=float(loc_row["longitude"]),
                ),
                timezone=loc_row["timezone"],
            )
            return UserPreferences(primary_location=location)

    async def set_primary_location(self, location: Location) -> None:
        await self.initialize()
        loc_id = f"{location.name.lower()}:{location.country.lower()}:{location.coordinates.latitude:.4f}:{location.coordinates.longitude:.4f}"
        created_at = datetime.now(UTC).isoformat()
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute(
                """
                INSERT INTO saved_locations (id, name, country, region, latitude, longitude, timezone, is_primary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    country=excluded.country,
                    region=excluded.region,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    timezone=excluded.timezone,
                    is_primary=1
                """,
                (
                    loc_id,
                    location.name,
                    location.country,
                    location.region,
                    location.coordinates.latitude,
                    location.coordinates.longitude,
                    location.timezone,
                    created_at,
                ),
            )
            await db.execute(
                """
                INSERT INTO user_preferences (id, primary_location_id)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET primary_location_id=excluded.primary_location_id
                """,
                (loc_id,),
            )
            await db.commit()

    async def clear_preferences(self) -> None:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("DELETE FROM user_preferences WHERE id = 1")
            await db.commit()

    async def get_opened_locations(self) -> list[Location]:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM opened_location_tabs ORDER BY position ASC, id ASC"
            ) as cur:
                rows = await cur.fetchall()
        locations: list[Location] = []
        for row in rows:
            locations.append(
                Location(
                    name=row["name"],
                    country=row["country"],
                    region=row["region"],
                    coordinates=Coordinates(
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                    ),
                    timezone=row["timezone"],
                )
            )
        return locations

    async def add_opened_location(self, location: Location) -> None:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id FROM opened_location_tabs WHERE name = ? AND country = ? AND latitude = ? AND longitude = ?",
                (
                    location.name,
                    location.country,
                    location.coordinates.latitude,
                    location.coordinates.longitude,
                ),
            ) as cur:
                existing = await cur.fetchone()
            if existing:
                await db.commit()
                return
            async with db.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM opened_location_tabs"
            ) as cur:
                row = await cur.fetchone()
            pos = row["next_pos"] if row else 0
            await db.execute(
                """
                INSERT INTO opened_location_tabs (name, country, region, latitude, longitude, timezone, position)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    location.name,
                    location.country,
                    location.region,
                    location.coordinates.latitude,
                    location.coordinates.longitude,
                    location.timezone,
                    pos,
                ),
            )
            await db.commit()

    async def remove_opened_location(self, location: Location) -> None:
        await self.initialize()
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute(
                "DELETE FROM opened_location_tabs WHERE name = ? AND country = ? AND latitude = ? AND longitude = ?",
                (
                    location.name,
                    location.country,
                    location.coordinates.latitude,
                    location.coordinates.longitude,
                ),
            )
            await db.commit()
