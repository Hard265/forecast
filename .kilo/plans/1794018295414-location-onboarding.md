# Plan: Initial location-selection (onboarding) screen

## Goal
On first launch (and whenever no default location has been saved), show a screen where the user selects or searches for their default location. Persist that choice so subsequent launches boot straight into the MainScreen for that location instead of hardcoding Blantyre.

## Decisions made
- **Persistence:** new `user_preferences` + `saved_locations` tables in `data/weather.db` via `aiosqlite`. Existing `data/weather.db` is untouched besides `CREATE TABLE IF NOT EXISTS`; no migration needed for old installs.
- **Search source:** hybrid — bundled static city list (offline first) + Open-Meteo Geocoding API (online, debounced). Falls back to bundled list only when offline/on error.
- **Defaults:** env-based `Settings.default_*` remain the fallback when nothing is saved; a saved primary location wins.
- **Scope:** initial screen only, plus a way to change later via the existing PinPanel tab (repurposed as "change home"). No multi-location forecast history, no alerting UI.

## Design

### Schema (new tables in `data/weather.db`)
```sql
CREATE TABLE IF NOT EXISTS saved_locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    region TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timezone TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    primary_location_id TEXT,
    FOREIGN KEY (primary_location_id) REFERENCES saved_locations(id)
);
```

### Domain model
Add `UserPreferences` (frozen dataclass: `primary_location: Location | None`) and reuse `SavedLocation` (already in `domain/models/app.py`) for saved locations.

### Layers
- `domain/models/preferences.py` — `UserPreferences`
- `application/repositories/user_preferences.py` — `UserPreferencesRepository` protocol (`get_preferences`, `set_primary_location`, `clear_preferences`)
- `infrastructure/repositories/sqlite_user_preferences.py` — aiosqlite implementation on `data/weather.db`
- `infrastructure/providers/open_meteo/geocoding.py` — `GeocodingClient` (httpx), `GeocodingResult` DTO, mapper to `Location`; base URL configurable via settings
- `data/cities.json` — bundled static list (name/country/lat/lon/timezone), offline fallback
- `ui/screens/location_picker.py` — `LocationPickerScreen(Screen[None])`: debounced search, list of bundled matches, geocoding hits merged/deduplicated, "Save as default" + quit or continue to MainScreen
- `ui/screens/main.py` — accept optional `location` override; keep working as before
- `app.py` — on mount, read preferences: if `primary_location` set, push `MainScreen(service, location)`; else push `LocationPickerScreen(service)` and, on select, persist and push `MainScreen`
- `composition_root.py` — wire `UserPreferencesRepository` + `GeocodingClient` into `create_weather_service` and `ForecastApp`

### Behavior details
- Debounce geocoding calls ~300ms per keystroke.
- Dedup geocoding results against bundled list by `(name, country, lat, lon)`.
- Empty query: show bundled list only.
- No internet: bundled list works; geocoding silently falls back.
- Picked location is saved as `primary` and used for the dashboard on next launch.
- PinPanel tab continues to work for quick viewing; add a "Change default location" affordance that reopens `LocationPickerScreen`.

## Ordered tasks
1. Add `tzdata` already done (runtime dep). Add `data/cities.json` bundled list (~25-50 cities).
2. Add `domain/models/preferences.py` (`UserPreferences`).
3. Add `application/repositories/user_preferences.py` protocol.
4. Add `infrastructure/repositories/sqlite_user_preferences.py` + `CREATE TABLE IF NOT EXISTS` in its `initialize()`.
5. Add `infrastructure/providers/open_meteo/geocoding.py` (client + DTO + mapper).
6. Add `application/config.py` fields: `geocoding_base_url`, `bundled_cities_path`.
7. Add `ui/screens/location_picker.py` screen.
8. Wire `app.py` to show picker when no primary location, else boot to MainScreen.
9. Wire `composition_root.py` to construct and pass the preferences repo / geocoding client.
10. Add tests: `tests/test_user_preferences.py` (sqlite CRUD), `tests/test_geocoding.py` (mock httpx + dedup), `tests/test_location_picker.py` (Textual `run_test` flow).
11. Update `pyproject.toml` dev/test deps if needed (none expected beyond current).

## Open questions / scope boundary
- PinPanel "Change default location" affordance: proposed as a button/menu on the PinPanel tab that reopens `LocationPickerScreen`. Confirm or mark out of scope.
- Should selecting a city in the picker also immediately show its weather (preview)? Proposed no: selection just saves and transitions. Confirm.
- Bundled list contents: proposed ~30 major world cities + the Blantyre/Lilongwe already hardcoded in PinPanel. Confirm curation.

## Validation
- `pytest -q` green; new sqlite tests run against `:memory:` db.
- `ruff check src tests` and `ruff format --check src tests` clean.
- `pyright src` clean.
- Manual: launch app, fresh `data/weather.db` -> picker shows bundled list; search returns bundled + mocked geocoding hits; select one; relaunch -> MainScreen boots to chosen location.

## Validation
- `pytest -q` green; new sqlite tests run against `:memory:` db.
- `ruff check src tests` and `ruff format --check src tests` clean.
- `pyright src` clean.
- Manual: launch app, fresh `data/weather.db` -> picker shows bundled list; search returns bundled + mocked geocoding hits; select one; relaunch -> MainScreen boots to chosen location.
