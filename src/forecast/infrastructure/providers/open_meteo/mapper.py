from datetime import datetime
from zoneinfo import ZoneInfo

from forecast.domain.models.atmospheric import AtmosphericConditions
from forecast.domain.models.conditions import WeatherCondition, WeatherDescription
from forecast.domain.models.current_weather import CurrentWeather
from forecast.domain.models.forecast import DailyForecast, Forecast, HourlyForecast
from forecast.domain.models.location import Location
from forecast.domain.models.precipitation import Precipitation
from forecast.domain.models.temperature import Temperature
from forecast.domain.models.wind import Wind
from forecast.infrastructure.providers.open_meteo.dto import OpenMeteoResponseDTO


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

    def _condition(self, code: int, is_day: bool = True) -> WeatherDescription:
        condition = self.WEATHER_CODES.get(code, WeatherCondition.UNKNOWN)
        return WeatherDescription(
            condition=condition,
            description=condition.value.replace("_", " ").title(),
            is_day=is_day,
        )

    def to_current_weather(
        self,
        response: OpenMeteoResponseDTO,
        location: Location,
    ) -> CurrentWeather:
        current = response.current
        observed_at = datetime.fromisoformat(current.time).replace(
            tzinfo=ZoneInfo(response.timezone)
        )

        return CurrentWeather(
            location=location,
            observed_at=observed_at,
            temperature=Temperature(
                current=current.temperature_2m,
                feels_like=current.apparent_temperature,
            ),
            conditions=self._condition(current.weather_code, bool(current.is_day)),
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
                probability=0.0,
                amount=current.precipitation,
                unit="mm",
            ),
        )

    def to_forecast(
        self,
        response: OpenMeteoResponseDTO,
        location: Location,
    ) -> Forecast:
        tz = ZoneInfo(response.timezone)
        hourly = response.hourly
        daily = response.daily

        hourly_forecasts = tuple(
            HourlyForecast(
                timestamp=datetime.fromisoformat(t).replace(tzinfo=tz),
                temperature=hourly.temperature_2m[i],
                feels_like=hourly.temperature_2m[i],
                condition=self._condition(
                    hourly.weather_code[i],
                    is_day=True,
                ),
                precipitation_probability=hourly.precipitation_probability[i] / 100.0,
                humidity=hourly.relative_humidity_2m[i],
                wind=Wind(
                    speed=hourly.wind_speed_10m[i],
                    direction=hourly.wind_direction_10m[i],
                    unit="km/h",
                ),
            )
            for i, t in enumerate(hourly.time)
        )

        daily_forecasts = tuple(
            DailyForecast(
                date=datetime.fromisoformat(d).replace(tzinfo=tz),
                temperature=Temperature(
                    current=daily.temperature_2m_max[i],
                    feels_like=daily.temperature_2m_max[i],
                    minimum=daily.temperature_2m_min[i],
                    maximum=daily.temperature_2m_max[i],
                ),
                condition=self._condition(daily.weather_code[i]),
                precipitation=Precipitation(
                    probability=daily.precipitation_probability_max[i] / 100.0,
                    amount=daily.precipitation_sum[i],
                    unit="mm",
                ),
                wind=Wind(
                    speed=daily.wind_speed_10m_max[i],
                    direction=daily.wind_direction_10m_dominant[i],
                    unit="km/h",
                ),
                sunrise=datetime.fromisoformat(daily.sunrise[i]).replace(tzinfo=tz),
                sunset=datetime.fromisoformat(daily.sunset[i]).replace(tzinfo=tz),
                uv_index=daily.uv_index_max[i],
            )
            for i, d in enumerate(daily.time)
        )

        return Forecast(
            location=location,
            hourly=hourly_forecasts,
            daily=daily_forecasts,
            generated_at=datetime.now(tz),
        )
