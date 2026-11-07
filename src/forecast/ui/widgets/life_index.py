"""Life index widget derived from current weather conditions."""

from __future__ import annotations

import contextlib

from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Static

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.errors import ForecastError
from forecast.domain.models.location import Location


class LifeIndex(Grid):
    DEFAULT_CSS = """
    LifeIndex {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 1;
        padding: 1;
        height: auto;
    }

    LifeIndex > .card {
        height: auto;
        background: $panel;
        border: tall $background;
        padding: 1 2;
        layout: vertical;
    }

    LifeIndex > .card > .label {
        color: $text-muted;
    }

    LifeIndex > .card > .value {
        text-style: bold;
    }
    """

    def __init__(
        self,
        service: DefaultWeatherService,
        location: Location,
    ) -> None:
        super().__init__()
        self._service = service
        self._location = location

    def compose(self) -> ComposeResult:
        for label, card_id in [
            ("Running", "running"),
            ("Clothing", "clothing"),
            ("Outdoor", "outdoor"),
            ("Comfort", "comfort"),
        ]:
            card = Vertical()
            card.add_class("card")
            yield card
            card.compose_add_child(Static(label, classes="label"))
            card.compose_add_child(Static("--", classes="value", id=f"li-{card_id}"))

    async def on_mount(self) -> None:
        try:
            snapshot = await self._service.get_weather_dashboard(self._location)
        except ForecastError:
            return
        except Exception:
            return

        current = snapshot.current
        temp = current.temperature.current
        humidity = current.atmospheric.humidity
        wind = current.wind.speed

        if temp < 5:
            running = "Too cold"
        elif temp > 30:
            running = "Too hot"
        elif wind > 25:
            running = "Too windy"
        else:
            running = "Good"

        if temp < 10:
            clothing = "Heavy jacket"
        elif temp < 20:
            clothing = "Light jacket"
        elif temp < 28:
            clothing = "T-shirt"
        else:
            clothing = "Light clothing"

        outdoor = "Poor" if humidity > 80 or temp > 32 or temp < 0 else "Good"

        if 18 <= temp <= 26 and humidity < 70:
            comfort = "Comfortable"
        elif humidity > 80:
            comfort = "Humid"
        elif temp > 30:
            comfort = "Hot"
        elif temp < 10:
            comfort = "Cold"
        else:
            comfort = "Fair"

        self._set("running", running)
        self._set("clothing", clothing)
        self._set("outdoor", outdoor)
        self._set("comfort", comfort)

    def _set(self, card_id: str, text: str) -> None:
        with contextlib.suppress(Exception):
            self.query_one(f"#li-{card_id}", Static).update(text)
