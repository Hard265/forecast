from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Digits, Static

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.errors import ForecastError
from forecast.domain.models.location import Location


class WeatherHero(Vertical):
    DEFAULT_CSS = """
    WeatherHero {
        height: auto;
        align: center middle;
        padding: 4 4;
        width: 100%;
    }

    WeatherHero Digits {
        width: 100%;
        text-align: center;
    }

    WeatherHero Static {
        width: 100%;
        text-align: center;
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
        self.add_class("p-md")

    def compose(self) -> ComposeResult:
        yield Digits("00°", id="temperature", classes="text-center")
        yield Static("", id="summary", classes="text-center")
        yield Static("", id="details", classes="text-center")

    async def on_mount(self) -> None:
        try:
            snapshot = await self._service.get_weather_dashboard(self._location)
            self._draw(snapshot)
        except ForecastError as exc:
            self._draw_error(str(exc))
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self._draw_error(str(exc))

    def _draw(self, snapshot) -> None:
        current = snapshot.current
        daily = snapshot.forecast.daily[0] if snapshot.forecast.daily else None

        self.query_one("#temperature", Digits).update(
            f"{round(current.temperature.current)}°"
        )

        summary = current.conditions.description
        if daily is not None:
            summary += f"  {round(daily.temperature.minimum)}°/{round(daily.temperature.maximum)}°"
        self.query_one("#summary", Static).update(f"[bold]{summary}[/bold]")

        details = (
            f"feels like {round(current.temperature.feels_like)} "
            f"{current.wind.direction:.0f}° wind {round(current.wind.speed)}"
        )
        self.query_one("#details", Static).update(details)

    def _draw_error(self, message: str) -> None:
        self.query_one("#temperature", Digits).update("--°")
        self.query_one("#summary", Static).update("[bold]Weather unavailable[/bold]")
        self.query_one("#details", Static).update(f"[red]{message}[/red]")
