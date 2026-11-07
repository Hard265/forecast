"""Unit conversion helpers for user preferences."""


def celsius_to_fahrenheit(value: float) -> float:
    return value * 9.0 / 5.0 + 32.0


def fahrenheit_to_celsius(value: float) -> float:
    return (value - 32.0) * 5.0 / 9.0


def kmh_to_ms(value: float) -> float:
    return value / 3.6


def ms_to_kmh(value: float) -> float:
    return value * 3.6


def mm_to_inches(value: float) -> float:
    return value / 25.4


def inches_to_mm(value: float) -> float:
    return value * 25.4


def temperature_symbol(prefs) -> str:
    if prefs is not None and getattr(prefs, "temperature_unit", "celsius") == "fahrenheit":
        return "°F"
    return "°C"


def convert_temperature(value: float, prefs) -> float:
    if prefs is not None and getattr(prefs, "temperature_unit", "celsius") == "fahrenheit":
        return celsius_to_fahrenheit(value)
    return value
