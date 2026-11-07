from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Static

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.errors import ForecastError
from forecast.domain.models.location import Location


class WeeklyForecast(Container):
    DEFAULT_CSS = """
    WeeklyForecast {
        padding: 0 1;
        margin: 1;
        background: $panel;
        border: tall $background;
        height: auto;
    }

    WeeklyForecast > #label {
        margin-bottom: 1;
        color: $text-muted;
    }

    WeeklyForecast DataTable {
        width: 100%;
        padding: 1 0;
        scrollbar-size-vertical: 2;
        scrollbar-size-horizontal: 1;
    }

    WeeklyForecast DataTable > .datatable--cell {
        padding: 0 1;
    }

    DataTable > .datatable--odd-row  { background: $surface; }
    DataTable > * { background: $panel; }
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
        yield Static("Next 7 days", id="label")
        yield DataTable(id="weekly-forecast")

    async def on_mount(self) -> None:
        try:
            snapshot = await self._service.get_weather_dashboard(self._location)
        except ForecastError:
            return

        from forecast.application.units import convert_temperature, temperature_symbol

        prefs = getattr(self.app, "preferences", None)
        sym = temperature_symbol(prefs)
        table = self.query_one(DataTable)
        table.expand = True
        table.cursor_type = "none"
        table.add_columns("date", "status", "temp(Min/Max)")
        for daily in snapshot.forecast.daily:
            low = daily.temperature.minimum
            high = daily.temperature.maximum
            if low is not None:
                low = convert_temperature(low, prefs)
            if high is not None:
                high = convert_temperature(high, prefs)
            low_str = f"{round(low)}{sym}" if low is not None else "—"
            high_str = f"{round(high)}{sym}" if high is not None else "—"
            table.add_row(
                daily.date.strftime("%a %d"),
                daily.condition.description.title(),
                f"{low_str}/{high_str}",
            )
