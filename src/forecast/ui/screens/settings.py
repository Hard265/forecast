"""Settings screen for unit preferences."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select, Static

from forecast.domain.models.preferences import UserPreferences

if TYPE_CHECKING:
    from forecast.app import ForecastApp


class SettingsScreen(ModalScreen[None]):
    BINDINGS = [("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        app = cast("ForecastApp", self.app)
        prefs = app.preferences
        with Vertical(id="settings-container"):
            yield Label("Settings", id="settings-title")
            yield Static("Temperature unit")
            yield Select(
                [("Celsius", "celsius"), ("Fahrenheit", "fahrenheit")],
                value=prefs.temperature_unit,
                id="temp-unit",
            )
            yield Static("Wind speed unit")
            yield Select(
                [("km/h", "km/h"), ("m/s", "m/s")],
                value=prefs.wind_speed_unit,
                id="wind-unit",
            )
            yield Static("Precipitation unit")
            yield Select(
                [("mm", "mm"), ("inches", "inches")],
                value=prefs.precipitation_unit,
                id="precip-unit",
            )
            yield Button("Save", id="save", variant="primary")
            yield Button("Cancel", id="cancel")

    async def on_button_pressed(self, event) -> None:
        if event.button.id == "cancel":
            self.dismiss()
            return
        if event.button.id == "save":
            app = cast("ForecastApp", self.app)
            temp = self.query_one("#temp-unit", Select).value
            wind = self.query_one("#wind-unit", Select).value
            precip = self.query_one("#precip-unit", Select).value
            prefs = UserPreferences(
                primary_location=app.preferences.primary_location,
                temperature_unit=str(temp),
                wind_speed_unit=str(wind),
                precipitation_unit=str(precip),
                use_24_hour_clock=app.preferences.use_24_hour_clock,
            )
            app.set_preferences(prefs)
            repo = getattr(app, "_prefs_repo", None)
            if repo is not None:
                with contextlib.suppress(Exception):
                    await repo.set_preferences(prefs)
            self.dismiss()
