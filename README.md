# Environment Tracker

A Streamlit dashboard that shows the current weather and a 5-day forecast for any city. Type a city name, pick it from the suggestions, and see live conditions, a daily summary, a temperature chart and an hourly table. The background changes with the weather.

## Features

- **City search with suggestions.** Type to filter about 12,000 cities (population 50,000 and up), offline, with no API calls.
- **Current conditions.** Temperature, feels-like, humidity, wind speed, pressure, sunrise and sunset, all in the city's local time.
- **5-day forecast.** A daily high/low and dominant condition, a temperature chart every 3 hours, and an expandable hourly table.
- **Weather-based background.** The colours change with the condition: blue for clear skies, navy for clear nights, slate for clouds, dark grey for rain, purple for storms, and icy blue for snow.
- **Error handling.** Clear messages for a missing or invalid API key, an unknown city, a timeout, no connection, rate limiting and server errors.
- **Cached requests.** Results are cached for 10 minutes per city, so repeat searches don't use extra API calls.

## Technology stack

| Technology | Used for |
| --- | --- |
| Python 3.11+ | Application logic |
| Streamlit | Web interface |
| OpenWeather API | Current weather and 5-day forecast |
| pandas | Organising forecast data and daily summaries |
| Plotly | Temperature chart |
| geonamescache | Offline city list for search suggestions |
| pytest | Automated tests |

## Getting an OpenWeather API key

1. Create an account at [openweathermap.org](https://openweathermap.org/).
2. Generate an API key in your account settings.
3. Check the plan's free-call limits and pricing. The app makes **2 calls per city search** (current weather and forecast), and results are cached for 10 minutes.

## Installation

Requires Python 3.11 or newer.

```bash
git clone https://github.com/<your-username>/python-weather-dashboard.git
cd python-weather-dashboard

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Copy the template and add your key:

```bash
cp .env.example .env
```

Edit `.env` so it contains your key:

```
OPENWEATHER_API_KEY=your_real_key_here
```


## Running the app

```bash
streamlit run app.py
```


## Running the tests

```bash
pytest
```

The tests mock the API, so they run without an API key or internet connection.



## Project structure

```
.
├── app.py                    # Streamlit dashboard (entry point)
├── requirements.txt
├── .env.example              # Template for the API key (safe to commit)
├── assets/
│   └── icons/
│       └── environmental.png # Browser tab icon
├── src/
│   ├── config.py             # Settings and API key lookup
│   ├── weather_api.py        # OpenWeather requests and error handling
│   ├── weather_processor.py  # Turns raw API data into display values
│   ├── cities.py             # Offline city list for suggestions
│   └── themes.py             # Background colours by weather condition
└── tests/
    ├── test_weather_api.py
    ├── test_weather_processor.py
    └── test_themes.py
```
