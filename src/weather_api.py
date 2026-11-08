"""Client for the OpenWeather current-weather and 5-day forecast endpoints."""

from __future__ import annotations

from typing import Any

import requests

from src import config

VALID_UNITS = ("metric", "imperial")


class WeatherAPIError(Exception):
    """Raised for any failure while fetching weather data.

    ``kind`` is one of: missing_key, invalid_key, city_not_found,
    rate_limited, server_error, timeout, connection, bad_response, invalid_input.
    """

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind
        self.message = message


def _request(url: str, city: str, units: str, api_key: str | None,
             session: requests.Session | None = None) -> dict[str, Any]:
    if units not in VALID_UNITS:
        raise WeatherAPIError("invalid_input", f"Unknown units: {units!r}")

    city = (city or "").strip()
    if not city:
        raise WeatherAPIError("invalid_input", "Please enter a city name.")

    key = (api_key if api_key is not None else config.OPENWEATHER_API_KEY).strip()
    if not key:
        raise WeatherAPIError(
            "missing_key",
            "No API key found. Add OPENWEATHER_API_KEY to your .env file.",
        )

    http = session or requests
    try:
        response = http.get(
            url,
            params={"q": city, "appid": key, "units": units},
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout as exc:
        raise WeatherAPIError(
            "timeout", "The weather service took too long to respond. Please try again."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise WeatherAPIError(
            "connection", "Could not connect to the weather service. Check your internet connection."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise WeatherAPIError("connection", f"Network error: {exc}") from exc

    status = response.status_code
    if status == 401:
        raise WeatherAPIError(
            "invalid_key",
            "Authentication failed. Check that your OpenWeather API key is correct and active.",
        )
    if status == 404:
        raise WeatherAPIError("city_not_found", f"City not found: '{city}'. Check the spelling.")
    if status == 429:
        raise WeatherAPIError("rate_limited", "Too many requests. Please wait a moment and try again.")
    if status >= 500:
        raise WeatherAPIError("server_error", "The weather service is having problems. Try again later.")
    if status != 200:
        raise WeatherAPIError("bad_response", f"Unexpected response from weather service (HTTP {status}).")

    try:
        data = response.json()
    except ValueError as exc:
        raise WeatherAPIError("bad_response", "The weather service returned invalid data.") from exc

    if not isinstance(data, dict):
        raise WeatherAPIError("bad_response", "The weather service returned invalid data.")
    return data


def get_current_weather(city: str, units: str = "metric", api_key: str | None = None,
                        session: requests.Session | None = None) -> dict[str, Any]:
    """Return the raw current-weather JSON for ``city``."""
    return _request(config.CURRENT_WEATHER_URL, city, units, api_key, session)


def get_forecast(city: str, units: str = "metric", api_key: str | None = None,
                 session: requests.Session | None = None) -> dict[str, Any]:
    """Return the raw 5-day / 3-hour forecast JSON for ``city``."""
    return _request(config.FORECAST_URL, city, units, api_key, session)
