from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.widgets import Digits, Static

from forecast.ui.widgets.daily_forecast import DailyForecast
from forecast.ui.widgets.weather_hero import WeatherHero
from forecast.ui.widgets.weekly_forecast import WeeklyForecast


class WeatherPanel(VerticalScroll):
    DEFAULT_CSS = """
    WeatherPanel {
        scrollbar-size-vertical: 1;
    }
    Vertical.forecast-container {
        margin: 2 3;
    }
    #cards {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        height: auto;
        margin: 1;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield WeatherHero()
        yield DailyForecast()
        yield WeeklyForecast()
        with Container(id="cards"):
            yield ForecastMetaCard()
            yield ForecastMetaCard()
            yield ForecastMetaCard()
            yield ForecastMetaCard()
            yield ForecastMetaCard()


class ForecastMetaCard(Vertical):
    DEFAULT_CSS = """
    ForecastMetaCard {
        background: $panel;
        padding: 1;
    }

    #digits-row {
        height: auto;
    }
    #digits-row Digits {
        text-align: center;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Precipitation")
        with Horizontal(id="digits-row"):
            yield Digits("43%")
        yield Static("Currently no precipitation")
