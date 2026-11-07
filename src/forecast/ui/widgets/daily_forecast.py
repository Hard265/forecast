from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, HorizontalScroll, Vertical
from textual.widgets import Static

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.errors import ForecastError
from forecast.domain.models.location import Location


class DailyForecast(Container):
    DEFAULT_CSS = """
    DailyForecast {
        padding: 0 1;
        margin: 1;
        background: $panel;
        border: tall $background;
        height: auto;
    }

    DailyForecast > #label {
        margin-bottom: 1;
        color: $text-muted;
    }

    HorizontalScroll {
        height: auto;
    }

    HorizontalScroll > * {
        height: 3;
        width: 8;
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
        yield Static("Next 24 Hours", id="label")
        with HorizontalScroll():
            for index in range(24):
                yield DailyForecastItem(index)

    async def on_mount(self) -> None:
        try:
            snapshot = await self._service.get_weather_dashboard(self._location)
            for index, hourly in enumerate(snapshot.forecast.hourly[:24]):
                item = self.query_one(f"#hour-{index}", DailyForecastItem)
                item.populate(hourly)
        except ForecastError:
            # WeatherHero already surfaces the error; leave the strip empty.
            pass


class DailyForecastItem(Vertical):
    DEFAULT_CSS = """
    DailyForecastItem {
        layout: vertical;
        height: auto;
    }
    """

    def __init__(self, index: int) -> None:
        super().__init__(id=f"hour-{index}")
        self._hourly = None

    def compose(self) -> ComposeResult:
        yield Static("Now", classes="time")
        yield Static("@", classes="icon")
        yield Static("[bold]00°[/bold]", classes="temp")

    def populate(self, hourly) -> None:
        self._hourly = hourly
        self.query_one(".time", Static).update(hourly.timestamp.strftime("%H:%M"))
        self.query_one(".icon", Static).update(self._icon_for(hourly.condition))
        self.query_one(".temp", Static).update(
            f"[bold]{round(hourly.temperature)}°[/bold]"
        )

    @staticmethod
    def _icon_for(condition) -> str:
        code = {
            "clear": "☀",
            "partly cloudy": "⛅",
            "cloudy": "☁",
            "overcast": "☁",
            "fog": "🌫",
            "drizzle": "🌦",
            "rain": "🌧",
            "heavy rain": "⛈",
            "snow": "🌨",
            "thunderstorm": "⛈",
            "unknown": "❓",
        }.get(condition.description.lower(), "❓")
        return code
