"""Domain-level errors for the forecast package.

Keeping errors in the domain layer means adapters and the UI can catch them
without importing infrastructure-specific exceptions.
"""

from __future__ import annotations


class ForecastError(Exception):
    """Base class for all forecast errors."""


class WeatherProviderError(ForecastError):
    """Raised when the upstream weather provider fails."""


class WeatherCacheError(ForecastError):
    """Raised when a cache operation fails."""


class LocationNotFoundError(ForecastError):
    """Raised when a requested location cannot be resolved."""


class ConfigurationError(ForecastError):
    """Raised when the application is misconfigured."""
