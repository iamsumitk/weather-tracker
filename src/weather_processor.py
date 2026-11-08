"""Turns raw OpenWeather JSON into clean, UI-friendly data.

Every extractor falls back to ``None`` / "N/A" when a field is missing, so the
UI never has to understand the raw API response.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

UNIT_SYMBOLS = {
    "metric": {"temp": "°C", "speed": "m/s"},
    "imperial": {"temp": "°F", "speed": "mph"},
}

NA = "N/A"


def _get(data: Any, *keys: Any, default: Any = None) -> Any:
    """Safely walk nested dicts/lists. ``_get(d, "main", "temp")``."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and isinstance(key, int) and -len(current) <= key < len(current):
            current = current[key]
        else:
            return default
    return default if current is None else current


def format_temperature(value: float | None, units: str = "metric") -> str:
    if value is None:
        return NA
    return f"{value:.1f} {UNIT_SYMBOLS[units]['temp']}"


def format_speed(value: float | None, units: str = "metric") -> str:
    if value is None:
        return NA
    return f"{value:.1f} {UNIT_SYMBOLS[units]['speed']}"


def format_humidity(value: float | None) -> str:
    return NA if value is None else f"{value:.0f}%"


def format_pressure(value: float | None) -> str:
    return NA if value is None else f"{value:.0f} hPa"


def _capitalize(text: str | None) -> str | None:
    return text[:1].upper() + text[1:] if text else None


def extract_current_weather(data: dict[str, Any], units: str = "metric") -> dict[str, Any]:
    """Pull the fields the dashboard needs from a current-weather response."""
    city = _get(data, "name", default="Unknown location")
    country = _get(data, "sys", "country")
    location = f"{city}, {country}" if country else city

    temp = _get(data, "main", "temp")
    feels = _get(data, "main", "feels_like")
    humidity = _get(data, "main", "humidity")
    pressure = _get(data, "main", "pressure")
    wind = _get(data, "wind", "speed")
    description = _capitalize(_get(data, "weather", 0, "description"))
    condition = _get(data, "weather", 0, "main")
    icon = _get(data, "weather", 0, "icon", default="")

    return {
        "icon": icon,
        "is_night": icon.endswith("n"),
        "location": location,
        "temperature": temp,
        "temperature_display": format_temperature(temp, units),
        "feels_like": feels,
        "feels_like_display": format_temperature(feels, units),
        "humidity": humidity,
        "humidity_display": format_humidity(humidity),
        "pressure": pressure,
        "pressure_display": format_pressure(pressure),
        "wind_speed": wind,
        "wind_speed_display": format_speed(wind, units),
        "description": description or NA,
        "condition": condition or NA,
        "sunrise": _local_time(data, _get(data, "sys", "sunrise")),
        "sunset": _local_time(data, _get(data, "sys", "sunset")),
    }


def _local_time(data: dict[str, Any], unix_ts: int | None) -> str:
    """Convert a UTC unix timestamp to the city's local HH:MM time."""
    if unix_ts is None:
        return NA
    offset = _get(data, "timezone", default=0)
    local = datetime.fromtimestamp(unix_ts, tz=timezone.utc) + timedelta(seconds=offset)
    return local.strftime("%H:%M")


def extract_forecast_intervals(data: dict[str, Any], units: str = "metric") -> pd.DataFrame:
    """Return one row per 3-hour forecast entry, in the city's local time."""
    offset = _get(data, "city", "timezone", default=0)
    rows = []
    for item in _get(data, "list", default=[]) or []:
        dt = _get(item, "dt")
        if dt is None:
            continue
        local_time = datetime.fromtimestamp(dt, tz=timezone.utc) + timedelta(seconds=offset)
        rows.append({
            "time": local_time.replace(tzinfo=None),
            "date": local_time.date(),
            "temperature": _get(item, "main", "temp"),
            "feels_like": _get(item, "main", "feels_like"),
            "humidity": _get(item, "main", "humidity"),
            "wind_speed": _get(item, "wind", "speed"),
            "condition": _get(item, "weather", 0, "main", default=NA),
            "description": _capitalize(_get(item, "weather", 0, "description", default=NA)),
        })

    columns = ["time", "date", "temperature", "feels_like", "humidity",
               "wind_speed", "condition", "description"]
    df = pd.DataFrame(rows, columns=columns)
    if not df.empty:
        df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    return df


def daily_summary(intervals: pd.DataFrame) -> pd.DataFrame:
    """Group 3-hour intervals by calendar date.

    The forecast gives intervals, not an exact daily high/low, so these are the
    highest and lowest interval temperatures seen that day, and the most
    frequent condition among that day's intervals.
    """
    columns = ["date", "max_temp", "min_temp", "condition"]
    if intervals.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for date, group in intervals.groupby("date", sort=True):
        temps = group["temperature"].dropna()
        conditions = group["condition"].dropna()
        conditions = conditions[conditions != NA]
        rows.append({
            "date": date,
            "max_temp": temps.max() if not temps.empty else None,
            "min_temp": temps.min() if not temps.empty else None,
            "condition": conditions.mode().iloc[0] if not conditions.empty else NA,
        })
    return pd.DataFrame(rows, columns=columns)
