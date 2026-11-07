from typing import Optional

from textual.app import App
from textual.binding import Binding

from forecast.ui.screens.main import MainScreen
from forecast.domain.repositories.weather_repository import DefaultWeatherRepository
from forecast.application.repositories.weather_repository import WeatherRepository


class ForecastApp(App[None]):
    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark theme"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, repo: Optional[WeatherRepository]):
        provider = 
        if not repo:
            repo = DefaultWeatherRepository()

    def action_toggle_dark(self):
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def on_mount(self):
        self.push_screen(MainScreen())
