from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input

from forecast.application.services.weather_service import DefaultWeatherService
from forecast.domain.models.location import Coordinates, Location
from forecast.ui.widgets.location_list import LocationItem, LocationList


class PinPanel(Vertical):
    def __init__(self, service: DefaultWeatherService) -> None:
        super().__init__()
        self._service = service
        self._query = ""
        self._locations = [
            Location(
                name="Blantyre",
                coordinates=Coordinates(latitude=-15.7833, longitude=35.0),
                country="Malawi",
                region="Southern",
                timezone="Africa/Blantyre",
            ),
            Location(
                name="Lilongwe",
                coordinates=Coordinates(latitude=-13.9833, longitude=33.7833),
                country="Malawi",
                region="Central",
                timezone="Africa/Blantyre",
            ),
        ]

    def compose(self) -> ComposeResult:
        yield LocationList(self._locations)
        yield Input(placeholder="Search country or region", id="search")

    async def on_list_view_selected(self, event: LocationList.Selected) -> None:
        if isinstance(event.item, LocationItem):
            location = event.item.location
            try:
                current = await self._service.get_current_weather(location)
                self.notify(f"{location.name}: {round(current.temperature.current)}°")
            except Exception as exc:  # pragma: no cover - UI feedback
                self.notify(f"Failed: {exc}", severity="error")

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._query = event.value
