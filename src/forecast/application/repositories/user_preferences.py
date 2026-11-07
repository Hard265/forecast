"""Application port for user preferences persistence."""

from __future__ import annotations

from typing import Protocol

from forecast.domain.models.location import Location
from forecast.domain.models.preferences import UserPreferences


class UserPreferencesRepository(Protocol):
    async def get_preferences(self) -> UserPreferences: ...

    async def set_primary_location(self, location: Location) -> None: ...

    async def set_preferences(self, preferences: "UserPreferences") -> None: ...

    async def clear_preferences(self) -> None: ...

    async def get_opened_locations(self) -> list[Location]: ...

    async def add_opened_location(self, location: Location) -> None: ...

    async def remove_opened_location(self, location: Location) -> None: ...
