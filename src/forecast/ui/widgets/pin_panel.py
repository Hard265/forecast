from __future__ import annotations

import asyncio
import contextlib
import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input

from forecast.application.config import load_settings
from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Coordinates, Location
from forecast.ui.widgets.location_list import LocationItem, LocationList


class PinPanel(Vertical):
    def __init__(self, service: DefaultWeatherService, main_screen=None) -> None:
        super().__init__()
        self._service = service
        self._main_screen = main_screen
        self._query = ""
        self._all_locations: list[Location] = []
        self._locations: list[Location] = []
        self._debounce_task: asyncio.Task[None] | None = None
        self._load_bundled()

    def _load_bundled(self) -> None:
        settings = load_settings()
        try:
            path = Path(settings.bundled_cities_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            data = json.loads(path.read_text())
            for item in data:
                self._all_locations.append(
                    Location(
                        name=item["name"],
                        country=item["country"],
                        region=item.get("region"),
                        coordinates=Coordinates(
                            latitude=float(item["latitude"]),
                            longitude=float(item["longitude"]),
                        ),
                        timezone=item.get("timezone") or "UTC",
                    )
                )
        except Exception:
            self._all_locations = [
                Location(
                    name="Blantyre",
                    coordinates=Coordinates(latitude=-15.7833, longitude=35.0),
                    country="Malawi",
                    region="Southern",
                    timezone="Africa/Blantyre",
                ),
                Location(
                    name="Lilongwe",
                    coordinates=Coordinates(latitude=-13.9833, longitude=33.7833),
                    country="Malawi",
                    region="Central",
                    timezone="Africa/Blantyre",
                ),
            ]
        self._locations = list(self._all_locations)

    def compose(self) -> ComposeResult:
        yield LocationList(self._locations)
        yield Input(placeholder="Search country or region", id="search")

    async def on_list_view_selected(self, event) -> None:
        # Handle both LocationList.Selected and ListView.Selected
        item = getattr(event, "item", None)
        if item is None and hasattr(event, "list_view"):
            try:
                idx = event.list_view.index
                if idx is not None and 0 <= idx < len(self._locations):
                    location = self._locations[idx]
                else:
                    return
            except Exception:
                return
        else:
            location = getattr(item, "location", None)
            if location is None and isinstance(item, LocationItem):
                location = item.location
        if location is None:
            return
        try:
            current = await self._service.get_current_weather(location)
            self.notify(f"{location.name}: {round(current.temperature.current)}°")
        except Exception as exc:  # pragma: no cover - UI feedback
            self.notify(f"Failed: {exc}", severity="error")
        if self._main_screen is not None and hasattr(
            self._main_screen, "add_location_tab"
        ):
            with contextlib.suppress(Exception):
                self._main_screen.add_location_tab(location)

    def on_mount(self) -> None:
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self._query.strip().lower()
        if not query:
            self._locations = list(self._all_locations)
        else:
            filtered = []
            for loc in self._all_locations:
                if (
                    query in loc.name.lower()
                    or query in loc.country.lower()
                    or (loc.region and query in loc.region.lower())
                ):
                    filtered.append(loc)
            self._locations = filtered
        self._refresh_list()

    def _refresh_list(self) -> None:
        try:
            location_list = self.query_one(LocationList)
            # Update locations and rebuild children
            location_list.locations = self._locations
            # Clear existing items
            location_list.remove_children()
            from forecast.ui.widgets.location_list import LocationItem

            for location in self._locations:
                item = LocationItem(location)
                item.location = location
                location_list.mount(item)
        except Exception:
            try:
                location_list = self.query_one(LocationList)
                location_list.locations = self._locations
                for child in list(location_list.children):
                    child.remove()
                for location in self._locations:
                    from forecast.ui.widgets.location_list import LocationItem

                    item = LocationItem(location)
                    item.location = location
                    location_list.mount(item)
            except Exception:
                pass

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._query = event.value
            if self._debounce_task and not self._debounce_task.done():
                self._debounce_task.cancel()
            self._debounce_task = asyncio.create_task(self._filter_debounced())

    async def _filter_debounced(self) -> None:
        await asyncio.sleep(0.15)
        self._apply_filter()
