from forecast.application.services.weather_service import WeatherService

def create_weather_service() -> WeatherService:

    http_client = OpenMeteoClient()
    mapper = OpenMeteoMapper()

    provider = OpenMeteoProvider(
        client=http_client,
        mapper=mapper,
    )

    memory_cache = MemoryWeatherCache()

    sqlite_cache = SQLiteWeatherCache(
        database_path="data/weather.db",
    )

    cache = TieredWeatherCache(
        memory=memory_cache,
        persistent=sqlite_cache,
    )

    repository = DefaultWeatherRepository(
        provider=provider,
        cache=cache,
    )

    return WeatherService(
        repository=repository,
    )
