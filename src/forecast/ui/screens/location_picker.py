"""Location picker screen for initial onboarding."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from forecast.application.config import Settings
from forecast.application.repositories.user_preferences import UserPreferencesRepository
from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Coordinates, Location
from forecast.infrastructure.providers.open_meteo.geocoding import GeocodingClient
from forecast.ui.screens.main import MainScreen


class LocationPickerScreen(Screen[None]):
    BINDINGS = [("escape", "quit", "Quit")]

    def __init__(
        self,
        service: DefaultWeatherService,
        preferences_repo: UserPreferencesRepository,
        geocoding_client: GeocodingClient,
        settings: Settings,
    ) -> None:
        super().__init__()
        self._service = service
        self._prefs = preferences_repo
        self._geocoding = geocoding_client
        self._settings = settings
        self._bundled: list[Location] = []
        self._results: list[Location] = []
        self._debounce_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-container"):
            yield Label("Select your default location", id="picker-title")
            yield Input(placeholder="Search for a city...", id="location-search")
            yield ListView(id="location-list")
            with Horizontal(id="picker-actions"):
                yield Button("Save as default", id="save-location", variant="primary")
                yield Button("Skip", id="skip-location")

    def on_mount(self) -> None:
        self._load_bundled()
        self._show_results(self._bundled)

    def _load_bundled(self) -> None:
        try:
            path = Path(self._settings.bundled_cities_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            data = json.loads(path.read_text())
            for item in data:
                self._bundled.append(
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
            self._bundled = []

    def _location_key(self, loc: Location) -> tuple[str, str, float, float]:
        return (
            loc.name.lower(),
            loc.country.lower(),
            round(float(loc.coordinates.latitude), 4),
            round(float(loc.coordinates.longitude), 4),
        )

    async def _search(self, query: str) -> None:
        q = query.strip()
        if not q:
            self._results = list(self._bundled)
            self._show_results(self._results)
            return
        merged: list[Location] = []
        seen = set()
        for loc in self._bundled:
            if q.lower() in loc.name.lower() or q.lower() in loc.country.lower():
                key = self._location_key(loc)
                if key not in seen:
                    seen.add(key)
                    merged.append(loc)
        try:
            geocoding_results = await self._geocoding.search(q)
            for gr in geocoding_results:
                loc = Location(
                    name=gr.name,
                    country=gr.country or "",
                    region=gr.admin1,
                    coordinates=Coordinates(latitude=gr.latitude, longitude=gr.longitude),
                    timezone=gr.timezone or "UTC",
                )
                key = self._location_key(loc)
                if key not in seen:
                    seen.add(key)
                    merged.append(loc)
        except Exception:
            pass
        self._results = merged
        self._show_results(self._results)

    def _show_results(self, results: list[Location]) -> None:
        list_view = self.query_one("#location-list", ListView)
        list_view.clear()
        for loc in results:
            label = f"{loc.name}, {loc.country}"
            if loc.region:
                label = f"{loc.name}, {loc.region}, {loc.country}"
            list_view.append(ListItem(Label(label), name=f"{loc.name}|{loc.country}"))
        if results:
            list_view.index = 0
            self._selected = results[0]
        else:
            self._selected = None

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "location-search":
            if self._debounce_task and not self._debounce_task.done():
                self._debounce_task.cancel()
            self._debounce_task = asyncio.create_task(self._debounced_search(event.value))

    async def _debounced_search(self, value: str) -> None:
        await asyncio.sleep(0.3)
        await self._search(value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        try:
            list_view = self.query_one("#location-list", ListView)
            idx = list_view.index if list_view.index is not None else 0
            if 0 <= idx < len(self._results):
                self._selected = self._results[idx]
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-location":
            if getattr(self, "_selected", None) is None and self._results:
                self._selected = self._results[0]
            if self._selected is None:
                self.notify("Select a location first", severity="error")
                return
            try:
                await self._prefs.set_primary_location(self._selected)
            except Exception as exc:
                self.notify(f"Failed to save: {exc}", severity="error")
                return
            self.app.pop_screen()
            self.app.push_screen(MainScreen(self._service, self._selected))
        elif event.button.id == "skip-location":
            # Use default from settings/env
            from forecast.infrastructure.composition_root import default_location

            loc = default_location(self._settings)
            try:
                await self._prefs.set_primary_location(loc)
            except Exception:
                pass
            self.app.pop_screen()
            self.app.push_screen(MainScreen(self._service, loc))

    def action_quit(self) -> None:
        self.app.exit()
