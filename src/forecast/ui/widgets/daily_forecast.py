from textual.containers import Container, HorizontalScroll, Vertical
from textual.widgets import Static


class DailyForecast(Container):
    DEFAULT_CSS = """
    DailyForecast {
        padding: 0 1;
        margin: 1;
        background: $panel;
        border: tall $background;
        height: auto;
    }

    DailyForecast > #label {
        margin-bottom: 1;
        color: $text-muted;
    }

    HorizontalScroll{
        height: auto;
    }

    HorizontalScroll > * {
        height: 3;
        width: 8;
    }

    """

    def compose(self):
        yield Static("Next 24 Hours", id="label")
        with HorizontalScroll():
            yield DailyForecastItem()
            yield DailyForecastItem()
            yield DailyForecastItem()
            yield DailyForecastItem()
            yield DailyForecastItem()
            yield DailyForecastItem()
            yield DailyForecastItem()
            yield DailyForecastItem()


class DailyForecastItem(Vertical):
    def compose(self):
        yield Static("Now")
        yield Static("@")
        yield Static("[bold]26°[bold]")
