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

    INDICES = [
        "Clothing",
        "Sun Protection",
        "Physical Activity",
        "Cold",
        "Travel",
        "Respiratory",
        "Mosquito",
        "Driving",
        "Makeup",
        "Comfort",
    ]

    def __init__(
        self,
        service: DefaultWeatherService,
        location: Location,
    ) -> None:
        super().__init__()
        self._service = service
        self._location = location

    def compose(self) -> ComposeResult:
        for label in self.INDICES:
            card_id = label.lower().replace(" ", "-")
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
        uv = current.uv_index if current.uv_index is not None else 0.0
        condition = current.conditions.description.lower()
        precip = current.precipitation.amount

        # Clothing
        if temp < 0:
            clothing = "Heavy winter"
        elif temp < 10:
            clothing = "Heavy jacket"
        elif temp < 18:
            clothing = "Light jacket"
        elif temp < 26:
            clothing = "T-shirt"
        else:
            clothing = "Light clothing"

        # Sun protection factor
        if uv < 3:
            sun = "Low"
        elif uv < 6:
            sun = "Moderate"
        elif uv < 8:
            sun = "High"
        elif uv < 11:
            sun = "Very high"
        else:
            sun = "Extreme"

        # Physical activity
        if temp < 0 or temp > 32 or wind > 30 or precip > 2:
            activity = "Poor"
        elif temp > 28 or humidity > 80:
            activity = "Fair"
        else:
            activity = "Good"

        # Cold (cold/flu risk)
        if temp < 5 and humidity > 70:
            cold = "High risk"
        elif temp < 10:
            cold = "Moderate"
        else:
            cold = "Low"

        # Travel
        if "thunder" in condition or "heavy rain" in condition or wind > 35:
            travel = "Difficult"
        elif "rain" in condition or "snow" in condition or "fog" in condition:
            travel = "Caution"
        else:
            travel = "Good"

        # Respiratory conditions
        if humidity > 85 or "fog" in condition:
            resp = "Poor"
        elif temp < 5:
            resp = "Fair"
        else:
            resp = "Good"

        # Mosquito
        if temp > 20 and humidity > 60 and precip == 0:
            mosquito = "High"
        elif temp > 15 and humidity > 50:
            mosquito = "Moderate"
        else:
            mosquito = "Low"

        # Driving
        if "heavy rain" in condition or "snow" in condition or "fog" in condition:
            driving = "Poor"
        elif "rain" in condition or "drizzle" in condition:
            driving = "Caution"
        else:
            driving = "Good"

        # Makeup
        if humidity > 75 or precip > 0:
            makeup = "Poor"
        elif temp > 30:
            makeup = "Fair"
        else:
            makeup = "Good"

        # Comfort
        if 18 <= temp <= 26 and humidity < 70 and wind < 15:
            comfort = "Comfortable"
        elif humidity > 80:
            comfort = "Humid"
        elif temp > 30:
            comfort = "Hot"
        elif temp < 10:
            comfort = "Cold"
        else:
            comfort = "Fair"

        values = {
            "clothing": clothing,
            "sun-protection": sun,
            "physical-activity": activity,
            "cold": cold,
            "travel": travel,
            "respiratory": resp,
            "mosquito": mosquito,
            "driving": driving,
            "makeup": makeup,
            "comfort": comfort,
        }
        for card_id, val in values.items():
            with contextlib.suppress(Exception):
                self.query_one(f"#li-{card_id}", Static).update(val)
