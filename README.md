# forecast

A Textual TUI weather application that fetches current conditions, hourly and
daily forecasts, and alerts from the [Open-Meteo](https://open-meteo.com/)
API, with a two-tier cache (in-memory + SQLite).

## Architecture

The codebase follows a **hexagonal (ports-and-adapters)** layout:

```
src/forecast/
├── domain/                    # pure domain models (no framework deps)
│   └── models/                # Forecast, CurrentWeather, Location, ...
├── application/               # use cases + ports (interfaces)
│   ├── services/weather_service.py   # DefaultWeatherService
│   ├── repositories/weather_repository.py  # WeatherRepository protocol
│   └── providers/weather_provider.py       # WeatherProvider protocol
├── infrastructure/            # outbound adapters
│   ├── providers/open_meteo/  # httpx client, DTO, mapper, provider
│   ├── cache/                 # memory, sqlite, tiered
│   ├── repositories/weather_repository.py  # DefaultWeatherRepository
│   └── composition_root.py    # dependency injection
└── ui/                        # textual widgets + screens
```

The only place concrete implementations are referenced is
`infrastructure/composition_root.py`, which makes wiring explicit and
testable.

## Running

```bash
uv pip install -e ".[dev]"
forecast            # launches the TUI
pytest              # runs the suite
ruff check src tests
ruff format --check src tests
pyright src
```

## Configuration

All settings are read from environment variables (see
`application/config.py`):

| Variable | Default | Description |
| --- | --- | --- |
| `OPEN_METEO_BASE_URL` | `https://api.open-meteo.com/v1/forecast` | API base URL |
| `OPEN_METEO_TIMEOUT_SECONDS` | `10` | request timeout |
| `OPEN_METEO_MAX_RETRIES` | `3` | transient-error retries |
| `FORECAST_CACHE_DIR` | `data` | writable cache directory |
| `FORECAST_SQLITE_CACHE_PATH` | `data/weather.db` | SQLite cache file |
| `FORECAST_CURRENT_TTL_SECONDS` | `600` | current-weather cache TTL |
| `FORECAST_FORECAST_TTL_SECONDS` | `1800` | forecast cache TTL |
| `FORECAST_DEFAULT_*` | Blantyre / -15.7833, 35.0 | default location |

## Testing

The suite covers models, caches, the Open-Meteo client (including retry and
backoff), the provider, the repository, the service, the composition root,
configuration, and the Textual UI (booted headless via `run_test()`).

```bash
pytest -q --cov=forecast --cov-report=term-missing
```