import contextlib
import hashlib

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, TabbedContent, TabPane

from forecast.application.repositories.user_preferences import UserPreferencesRepository
from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Location
from forecast.ui.widgets.daily_forecast import DailyForecast
from forecast.ui.widgets.pin_panel import PinPanel
from forecast.ui.widgets.weather_details import WeatherDetails
from forecast.ui.widgets.weather_hero import WeatherHero
from forecast.ui.widgets.weekly_forecast import WeeklyForecast
from forecast.ui.screens.settings import SettingsScreen


class MainScreen(Screen[None]):
    TITLE = "Forecast"

    BINDINGS = [("r", "refresh", "Refresh"), ("s", "settings", "Settings")]

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    MainScreen Header {
        dock: top;
    }
    MainScreen TabbedContent {
        dock: top;
        height: auto;
    }
    MainScreen Footer {
        dock: bottom;
    }
    MainScreen VerticalScroll {
        height: 1fr;
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
        self._location_tabs: dict[str, Location] = {}
        self._prefs_repo: UserPreferencesRepository | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="weather"):  # noqa: SIM117
            with TabPane(self._location.name, id="weather"):  # noqa: SIM117
                with VerticalScroll():
                    yield WeatherHero(self._service, self._location)
                    yield DailyForecast(self._service, self._location)
                    yield WeeklyForecast(self._service, self._location)
                    yield WeatherDetails(self._service, self._location)
            with TabPane("Pinned", id="pinned"):
                yield PinPanel(self._service, self)
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._restore_opened_tabs(), exclusive=False)

    async def _restore_opened_tabs(self) -> None:
        if self._prefs_repo is None:
            return
        try:
            opened = await self._prefs_repo.get_opened_locations()
        except Exception:
            return
        for loc in opened:
            self.add_location_tab(loc, persist=False)

    def add_location_tab(self, location: Location, persist: bool = True) -> None:
        stable = f"{location.name}|{location.country}|{location.coordinates.latitude}|{location.coordinates.longitude}"
        digest = hashlib.sha1(stable.encode()).hexdigest()[:8]
        tab_id = f"loc-{location.name.lower().replace(' ', '-')}-{digest}"
        if tab_id in self._location_tabs:
            try:
                tabs = self.query_one(TabbedContent)
                tabs.active = tab_id
            except Exception:
                pass
            if persist and self._prefs_repo is not None:
                with contextlib.suppress(Exception):
                    self.run_worker(
                        self._prefs_repo.add_opened_location(location), exclusive=False
                    )
            return
        pane = TabPane(location.name, id=tab_id)
        hero = WeatherHero(self._service, location)
        daily = DailyForecast(self._service, location)
        weekly = WeeklyForecast(self._service, location)
        details = WeatherDetails(self._service, location)
        with VerticalScroll() as vs:
            vs.compose_add_child(hero)
            vs.compose_add_child(daily)
            vs.compose_add_child(weekly)
            vs.compose_add_child(details)
        pane.compose_add_child(vs)
        try:
            tabs = self.query_one(TabbedContent)
            try:
                tabs.add_pane(pane, before="pinned")
            except Exception:
                with contextlib.suppress(Exception):
                    tabs.add_pane(pane)
            tabs.active = tab_id
            self._location_tabs[tab_id] = location
        except Exception:
            pass
        if persist and self._prefs_repo is not None:
            with contextlib.suppress(Exception):
                self.run_worker(
                    self._prefs_repo.add_opened_location(location), exclusive=False
                )

    async def action_refresh(self) -> None:
        """Re-fetch weather for the current screen by reloading it."""
        try:
            tabs = self.query_one(TabbedContent)
            active_tab = tabs.active
        except Exception:
            active_tab = None
        loc = (
            self._location_tabs.get(active_tab, self._location)
            if active_tab
            else self._location
        )
        # Force a fresh upstream fetch so widgets do not reuse stale cache.
        await self._service.get_weather_dashboard(loc, refresh=True)
        new_screen = MainScreen(self._service, loc)
        new_screen._prefs_repo = self._prefs_repo
        # Restore any previously opened tabs.
        for tab_loc in self._location_tabs.values():
            if tab_loc is not loc:
                new_screen.add_location_tab(tab_loc, persist=False)
        self.app.pop_screen()
        self.app.push_screen(new_screen)

    def action_settings(self) -> None:
        self.app.push_screen(SettingsScreen())
