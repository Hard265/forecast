from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Location
from forecast.ui.widgets.daily_forecast import DailyForecast
from forecast.ui.widgets.weather_hero import WeatherHero
from forecast.ui.widgets.weekly_forecast import WeeklyForecast


class MainScreen(Screen[None]):
    TITLE = "Forecast"

    def __init__(
        self,
        service: DefaultWeatherService,
        location: Location,
    ) -> None:
        super().__init__()
        self._service = service
        self._location = location

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            WeatherHero(self._service, self._location),
            DailyForecast(self._service, self._location),
            WeeklyForecast(self._service, self._location),
        )
        yield Footer()
