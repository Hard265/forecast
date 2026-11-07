from textual.app import ComposeResult
from textual.containers import VerticalScroll

from forecast.ui.widgets.daily_forecast import DailyForecast
from forecast.ui.widgets.weather_hero import WeatherHero
from forecast.ui.widgets.weekly_forecast import WeeklyForecast


class WeatherPanel(VerticalScroll):
    DEFAULT_CSS = """
    WeatherPanel {
        scrollbar-size-vertical: 1;
    }
    """

    def __init__(self, service, location) -> None:
        super().__init__()
        self._service = service
        self._location = location

    def compose(self) -> ComposeResult:
        yield WeatherHero(self._service, self._location)
        yield DailyForecast(self._service, self._location)
        yield WeeklyForecast(self._service, self._location)
