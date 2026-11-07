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

        table = self.query_one(DataTable)
        table.cursor_type = "none"
        table.add_columns("date", "status", "temp(Min/Max)")
        for daily in snapshot.forecast.daily:
            low = daily.temperature.minimum
            high = daily.temperature.maximum
            low_str = f"{round(low)}°" if low is not None else "—"
            high_str = f"{round(high)}°" if high is not None else "—"
            table.add_row(
                daily.date.strftime("%a %d"),
                daily.condition.description.title(),
                f"{low_str}/{high_str}",
            )
