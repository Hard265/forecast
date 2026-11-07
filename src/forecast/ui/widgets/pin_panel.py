from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input

from forecast.domain.models.location import Coordinates, Location
from forecast.ui.widgets.location_list import LocationItem, LocationList


class PinPanel(Vertical):
    def __init__(self):
        super().__init__()
        self._query = ""
        locations = [
            Location(
                name="Blantyre",
                coordinates=Coordinates(
                    latitude=2.3,
                    longitude=5.3,
                ),
                country="Malawi",
                region="sounthen",
                timezone="CAT",
            ),
            Location(
                name="Lilongwe",
                coordinates=Coordinates(
                    latitude=2.3,
                    longitude=5.3,
                ),
                country="Malawi",
                region="sounthen",
                timezone="CAT",
            ),
        ]
        self._locations = locations

    def compose(self) -> ComposeResult:
        yield LocationList(self._locations)
        yield Input(placeholder="Search country or region", id="search")

    def on_list_view_selected(self, event: LocationList.Selected):
        if isinstance(event.item, LocationItem):
            location = event.item.location
            self.notify(f"Selected {location.coordinates.latitude}")

    async def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search":
            self._query = event.value
