from textual.app import App
from textual.binding import Binding

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Location
from forecast.infrastructure.composition_root import (
    create_weather_service,
    default_location,
)
from forecast.ui.screens.main import MainScreen


class ForecastApp(App[None]):
    """The Textual TUI entrypoint.

    The application accepts an injected :class:`DefaultWeatherService` so the
    composition root can be swapped (e.g. for tests). On unmount it closes the
    underlying HTTP client to avoid leaking connections.
    """

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark theme"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, service: DefaultWeatherService | None = None) -> None:
        super().__init__()
        self._service = service or create_weather_service()
        self._location: Location = default_location()

    @property
    def service(self) -> DefaultWeatherService:
        return self._service

    @property
    def location(self) -> Location:
        return self._location

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self._service, self._location))

    async def on_unmount(self) -> None:
        """Release HTTP resources when the app shuts down."""
        provider = getattr(self._service._repository, "_provider", None)
        if provider is not None and hasattr(provider, "close"):
            await provider.close()
