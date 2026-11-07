from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, DataTable, Static


ROWS = [
    ("date", "status", "temp(Min/Max)"),
    ("Today", "[bold]Cloudy[bold]", "18°/[bold]23°[bold]"),
    ("Nov 6", "[bold]Overcast[bold]", "12°/[bold]20°[bold]"),
    ("Nov 7", "[bold]Overcast[bold]", "15°/[bold]18°[bold]"),
]


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

    def compose(self) -> ComposeResult:
        yield Static("Next 7 days", id="label")
        yield DataTable(
            id="weekly-forecast",
        )

    def on_mount(self):
        table = self.query_one(DataTable)
        table.cursor_type = "none"
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])
