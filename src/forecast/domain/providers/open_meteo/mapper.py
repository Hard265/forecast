from datetime import datetime
from zoneinfo import ZoneInfo

from forecast.domain.models.atmospheric import AtmosphericConditions
from forecast.domain.models.conditions import WeatherCondition, WeatherDescription
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.location import Location
from forecast.domain.models.precipitation import Precipitation
from forecast.domain.models.temperature import Temperature
from forecast.domain.models.wind import Wind
from forecast.domain.providers.open_meteo.dto import OpenMeteoResponseDTO

class OpenMeteoMapper:

    WEATHER_CODES = {
        0: WeatherCondition.CLEAR,
        1: WeatherCondition.PARTLY_CLOUDY,
        2: WeatherCondition.PARTLY_CLOUDY,
        3: WeatherCondition.OVERCAST,
        45: WeatherCondition.FOG,
        48: WeatherCondition.FOG,
        51: WeatherCondition.DRIZZLE,
        53: WeatherCondition.DRIZZLE,
        55: WeatherCondition.DRIZZLE,
        61: WeatherCondition.RAIN,
        63: WeatherCondition.RAIN,
        65: WeatherCondition.HEAVY_RAIN,
        71: WeatherCondition.SNOW,
        73: WeatherCondition.SNOW,
        75: WeatherCondition.SNOW,
        95: WeatherCondition.THUNDERSTORM,
        96: WeatherCondition.THUNDERSTORM,
        99: WeatherCondition.THUNDERSTORM,
    }

    def to_current_weather(
        self,
        response: OpenMeteoResponseDTO,
        location: Location,
    ) -> CurrentWeather:

        current = response.current

        observed_at = datetime.fromisoformat(
            current.time
        ).replace(
            tzinfo=ZoneInfo(response.timezone)
        )

        condition = self.WEATHER_CODES.get(
            current.weather_code,
            WeatherCondition.UNKNOWN,
        )

        return CurrentWeather(
            location=location,
            observed_at=observed_at,
            temperature=Temperature(
                current=current.temperature_2m,
                feels_like=current.apparent_temperature,
            ),
            conditions=WeatherDescription(
                condition=condition,
                description=condition.value.replace("_", " ").title(),
                is_day=bool(current.is_day),
            ),
            atmospheric=AtmosphericConditions(
                humidity=current.relative_humidity_2m,
                pressure=current.pressure_msl,
                visibility=None,
                cloud_cover=current.cloud_cover,
            ),
            wind=Wind(
                speed=current.wind_speed_10m,
                direction=current.wind_direction_10m,
                gust=current.wind_gusts_10m,
                unit="km/h",
            ),
            precipitation=Precipitation(
                probability=0.0,  # Not provided by current response
                amount=current.precipitation,
                unit="mm",
            ),
        )
