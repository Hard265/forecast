import contextlib

from textual.app import App
from textual.binding import Binding

from forecast.application.config import load_settings
from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Location
from forecast.infrastructure.composition_root import (
    create_geocoding_client,
    create_user_preferences_repository,
    create_weather_service,
    default_location,
)
from forecast.ui.screens.location_picker import LocationPickerScreen
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

    def __init__(
        self,
        service: DefaultWeatherService | None = None,
        location: Location | None = None,
    ) -> None:
        super().__init__()
        self.theme = "dracula"
        self._settings = load_settings()
        self._service = service or create_weather_service(self._settings)
        self._location: Location | None = location
        self._prefs_repo = create_user_preferences_repository(self._settings)
        self._geocoding = create_geocoding_client(self._settings)
        self._injected_service = service is not None

    @property
    def service(self) -> DefaultWeatherService:
        return self._service

    @property
    def location(self) -> Location | None:
        return self._location

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def on_mount(self) -> None:
        if self._injected_service and self._location is not None:
            screen = MainScreen(self._service, self._location)
            screen._prefs_repo = self._prefs_repo
            self.push_screen(screen)
            return
        if self._injected_service and self._location is None:
            # Backward compatible: tests inject service expecting MainScreen with default location
            screen = MainScreen(self._service, default_location(self._settings))
            screen._prefs_repo = self._prefs_repo
            self.push_screen(screen)
            return
        self.run_worker(self._boot(), exclusive=True)

    async def _boot(self) -> None:
        try:
            if self._location is not None:
                screen = MainScreen(self._service, self._location)
                screen._prefs_repo = self._prefs_repo
                self.push_screen(screen)
                return
            prefs = await self._prefs_repo.get_preferences()
            if prefs.primary_location is not None:
                screen = MainScreen(self._service, prefs.primary_location)
                screen._prefs_repo = self._prefs_repo
                self.push_screen(screen)
                return
            self.push_screen(
                LocationPickerScreen(
                    self._service,
                    self._prefs_repo,
                    self._geocoding,
                    self._settings,
                )
            )
        except Exception:
            # Fall back to default location if anything goes wrong
            loc = default_location(self._settings)
            screen = MainScreen(self._service, loc)
            screen._prefs_repo = self._prefs_repo
            self.push_screen(screen)

    async def on_unmount(self) -> None:
        """Release HTTP resources when the app shuts down."""
        provider = getattr(self._service._repository, "_provider", None)
        if provider is not None and hasattr(provider, "close"):
            with contextlib.suppress(Exception):
                await provider.close()
        with contextlib.suppress(Exception):
            await self._geocoding.close()
