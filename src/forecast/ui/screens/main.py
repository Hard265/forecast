from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, TabPane, TabbedContent

from forecast.ui.widgets.pin_panel import PinPanel
from forecast.ui.widgets.weather_panel import WeatherPanel


class MainScreen(Screen[None]):
    TITLE = "Forecast"
    CSS_PATH = "./../styles/weather_hero.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with TabbedContent():
                with TabPane("Blantyre"):
                    yield WeatherPanel()
                with TabPane("+ Pin"):
                    yield PinPanel()
        yield Footer()
