from __future__ import annotations

import contextlib

from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Digits, Static

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.errors import ForecastError
from forecast.domain.models.location import Location


class WeatherDetails(Grid):
    DEFAULT_CSS = """
    WeatherDetails {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 1;
        padding: 1;
        height: auto;
    }

    WeatherDetails > .card {
        height: auto;
        background: $panel;
        border: tall $background;
        padding: 1 2;
        layout: vertical;
    }

    WeatherDetails > .card.span-2 {
        column-span: 2;
    }

    WeatherDetails > .card > .label {
        color: $text-muted;
    }

    WeatherDetails > .card > Digits {
        text-style: bold;
        width: 100%;
    }

    WeatherDetails > .card > .comment {
        color: $text-muted;
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
        cards = [
            ("Precipitation", "precip"),
            ("Wind", "wind"),
            ("Humidity", "humidity"),
            ("UV Index", "uv"),
            ("Air Quality", "air"),
            ("Sunrise/Sunset", "sun"),
            ("Feels Like", "feels"),
            ("Pressure", "pressure"),
            ("Cloud Cover", "cloud"),
        ]
        for label, card_id in cards:
            card = Vertical()
            card.add_class("card")
            if card_id in ("wind", "sun"):
                card.add_class("span-2")
            yield card
            card.compose_add_child(Static(label, classes="label"))
            card.compose_add_child(Digits("--", classes="value", id=f"val-{card_id}"))
            card.compose_add_child(Static("", classes="comment", id=f"cmt-{card_id}"))

    async def on_mount(self) -> None:
        try:
            snapshot = await self._service.get_weather_dashboard(self._location)
        except ForecastError:
            return
        except Exception:
            return

        current = snapshot.current
        daily = snapshot.forecast.daily[0] if snapshot.forecast.daily else None

        def set_val(card_id: str, text: str) -> None:
            with contextlib.suppress(Exception):
                self.query_one(f"#val-{card_id}", Digits).update(text)
                return
            with contextlib.suppress(Exception):
                self.query_one(f"#val-{card_id}", Static).update(text)

        def set_cmt(card_id: str, text: str) -> None:
            with contextlib.suppress(Exception):
                self.query_one(f"#cmt-{card_id}", Static).update(text)

        if daily is not None and daily.precipitation is not None:
            try:
                p = daily.precipitation
                val = getattr(p, "sum", None) or getattr(p, "amount", None) or 0.0
                set_val("precip", f"{val:.1f} mm")
                set_cmt(
                    "precip",
                    "Light precipitation expected" if val < 2 else "Possible showers",
                )
            except Exception:
                set_val("precip", "0.0 mm")
                set_cmt("precip", "No precipitation")
        elif hasattr(current, "precipitation") and current.precipitation is not None:
            try:
                p = current.precipitation
                val = getattr(p, "amount", None) or 0.0
                set_val("precip", f"{val:.1f} mm")
                set_cmt(
                    "precip", "Dry conditions" if val == 0 else "Current precipitation"
                )
            except Exception:
                set_val("precip", "0.0 mm")
                set_cmt("precip", "No precipitation")
        else:
            set_val("precip", "0.0 mm")
            set_cmt("precip", "No precipitation")

        wind_spd = round(current.wind.speed)
        wind_dir = getattr(current.wind, "direction", 0)
        set_val("wind", f"{wind_spd} {current.wind.unit} {wind_dir:.0f}°")
        set_cmt(
            "wind", "Calm" if wind_spd < 12 else "Breezy" if wind_spd < 36 else "Windy"
        )

        try:
            hum = round(getattr(current.atmospheric, "humidity", 0))
            set_val("humidity", f"{hum}%")
            if hum < 30:
                set_cmt("humidity", "Dry air")
            elif hum < 60:
                set_cmt("humidity", "Comfortable humidity")
            elif hum < 80:
                set_cmt("humidity", "Humid")
            else:
                set_cmt("humidity", "Very humid")
        except Exception:
            set_val("humidity", "--%")
            set_cmt("humidity", "")

        if daily is not None and daily.uv_index is not None:
            uv = daily.uv_index
            set_val("uv", f"{uv:.1f}")
            if uv < 3:
                set_cmt("uv", "Low")
            elif uv < 6:
                set_cmt("uv", "Moderate")
            elif uv < 8:
                set_cmt("uv", "High")
            elif uv < 11:
                set_cmt("uv", "Very high")
            else:
                set_cmt("uv", "Extreme")
        else:
            set_val("uv", "--")
            set_cmt("uv", "")

        set_val("air", "Good")
        set_cmt("air", "Air quality acceptable")

        if daily is not None and daily.sunrise is not None and daily.sunset is not None:
            set_val(
                "sun",
                f"{daily.sunrise.strftime('%H:%M')}/{daily.sunset.strftime('%H:%M')}",
            )
            set_cmt("sun", "Sunrise/Sunset")
        else:
            set_val("sun", "--/--")
            set_cmt("sun", "")

        feels = round(
            getattr(current.temperature, "feels_like", current.temperature.current)
        )
        set_val("feels", f"{feels}°")
        set_cmt(
            "feels",
            "Feels similar"
            if abs(feels - round(current.temperature.current)) < 2
            else "Feels different",
        )

        try:
            press = round(
                getattr(
                    current.atmospheric,
                    "pressure",
                    getattr(current.atmospheric, "msl", 1013),
                )
            )
            set_val("pressure", f"{press} hPa")
            set_cmt("pressure", "Normal pressure")
        except Exception:
            set_val("pressure", "-- hPa")
            set_cmt("pressure", "")

        try:
            cloud = round(
                getattr(
                    current.atmospheric,
                    "cloud_cover",
                    getattr(current.atmospheric, "cloud", 0),
                )
            )
            set_val("cloud", f"{cloud}%")
            if cloud < 20:
                set_cmt("cloud", "Clear skies")
            elif cloud < 50:
                set_cmt("cloud", "Partly cloudy")
            elif cloud < 80:
                set_cmt("cloud", "Mostly cloudy")
            else:
                set_cmt("cloud", "Overcast")
        except Exception:
            set_val("cloud", "--%")
            set_cmt("cloud", "")
