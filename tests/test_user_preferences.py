"""Tests for user preferences persistence."""

from __future__ import annotations

import pytest

from forecast.domain.models.location import Coordinates, Location
from forecast.infrastructure.repositories.sqlite_user_preferences import (
    SqliteUserPreferencesRepository,
)


@pytest.mark.asyncio
async def test_preferences_crud(tmp_path) -> None:
    repo = SqliteUserPreferencesRepository(database_path=tmp_path / "prefs.db")
    prefs = await repo.get_preferences()
    assert prefs.primary_location is None

    loc = Location(
        name="Blantyre",
        country="Malawi",
        region="Southern",
        coordinates=Coordinates(latitude=-15.7861, longitude=35.0058),
        timezone="Africa/Blantyre",
    )
    await repo.set_primary_location(loc)
    prefs2 = await repo.get_preferences()
    assert prefs2.primary_location is not None
    assert prefs2.primary_location.name == "Blantyre"
    assert prefs2.primary_location.country == "Malawi"

    await repo.clear_preferences()
    prefs3 = await repo.get_preferences()
    assert prefs3.primary_location is None
