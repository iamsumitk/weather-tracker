"""Application configuration loaded from environment variables / .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from the project root if present (it is git-ignored).
load_dotenv(PROJECT_ROOT / ".env")

def _load_api_key() -> str:
    """Read the key from the environment or .env first, then Streamlit secrets (used on Streamlit Cloud)."""
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st

        return str(st.secrets.get("OPENWEATHER_API_KEY", "")).strip()
    except Exception:
        return ""


OPENWEATHER_API_KEY = _load_api_key()

CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

REQUEST_TIMEOUT_SECONDS = 10

DEFAULT_CITIES = ["Marburg", "Frankfurt", "Berlin"]
