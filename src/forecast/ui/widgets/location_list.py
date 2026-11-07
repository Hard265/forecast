from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, ListItem, ListView

from forecast.domain.models.location import Location


class LocationList(ListView):
    def __init__(self, locations: Sequence[Location]) -> None:
        self.locations = locations
        super().__init__()

    def compose(self) -> ComposeResult:
        for location in self.locations:
            item = LocationItem(location)
            item.location = location
            yield item


class LocationItem(ListItem):
    DEFAULT_CSS = """
    LocationItem {
        height: auto;
        padding: 1 2;
        layout: vertical;
    }

    LocationItem .row {
        height: 1;
    }

    LocationItem .location-name {
        width: 1fr;
        text-style: bold;
    }

    LocationItem .temperature {
        width: auto;
        margin-left: 2;
        text-style: bold;
    }

    LocationItem .location-details {
        width: 1fr;
        color: $text-muted;
    }
    """

    def __init__(self, location: Location) -> None:
        super().__init__()
        self.location = location

    def compose(self) -> ComposeResult:
        with Horizontal(classes="row"):
            yield Label(self.location.name, classes="location-name")
            yield Label("—", classes="temperature")
        with Horizontal(classes="row"):
            yield Label(self.location.timezone, classes="location-details")
