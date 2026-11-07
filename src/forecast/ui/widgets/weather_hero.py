from textual.containers import Vertical
from textual.widgets import Digits, Static


class WeatherHero(Vertical):
    DEFAULT_CSS = """
    WeatherHero {
        height: auto;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.classes = "p-md"

    def compose(self):
        yield Digits("50°", id="temperature", classes="text-center")
        yield Static("[bold]Cloudy 18°/30°[bold]", classes="text-center")
        yield Static("feels like 28 North wind scale 1", classes="text-center")
