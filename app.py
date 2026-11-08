import plotly.express as px
import streamlit as st

from src import config
from src.cities import city_options, to_query
from src.themes import background_gradient
from src.weather_api import WeatherAPIError, get_current_weather, get_forecast
from src.weather_processor import (
    NA,
    daily_summary,
    extract_current_weather,
    extract_forecast_intervals,
)

PAGE_ICON = str(config.PROJECT_ROOT / "assets" / "icons" / "environmental.png")

st.set_page_config(page_title="Environment Tracker", layout="wide", page_icon=PAGE_ICON)


def theme_css(gradient: tuple[str, str, str]) -> str:
    start, mid, end = gradient
    return f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {start} 0%, {mid} 50%, {end} 100%);
        color: #f5f7fa;
        transition: background 0.8s ease;
    }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    .env-banner {{
        background: linear-gradient(90deg, #11998e, #38ef7d);
        border-radius: 18px;
        padding: 22px 28px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        color: #0b1d1a;
    }}
    .env-banner h1 {{ margin: 0; font-size: 2.1rem; color: #0b1d1a; }}
    .env-banner p {{ margin: 4px 0 0 0; font-size: 1.05rem; color: #103a33; }}
    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 14px;
        padding: 14px 18px;
    }}
    [data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] {{ color: #f5f7fa; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 14px;
    }}
    .temp-hero {{ font-size: 4.5rem; font-weight: 700; line-height: 1; margin: 6px 0; }}
    </style>
    """


def banner_html() -> str:
    return """
<div class="env-banner">
    <h1>Environment Tracker</h1>
    <p>Live weather and forecasts for the cities you choose</p>
</div>
"""


# Header and background slot, filled again once the weather has loaded.
theme_slot = st.empty()
theme_slot.markdown(theme_css(background_gradient(None)) + banner_html(), unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner=False)
def load_weather(city: str, units: str) -> tuple[dict, dict]:
    current = get_current_weather(city, units)
    forecast = get_forecast(city, units)
    return current, forecast


# Search bar directly under the heading. Type to filter the suggestions;
# any name not in the list is also accepted.
city_choice = st.selectbox(
    "Search for a city",
    options=city_options(),
    index=None,
    placeholder="Start typing a city...",
    accept_new_options=True,
)

units = "metric"  # Celsius only

if not config.OPENWEATHER_API_KEY:
    st.error(
        "No OpenWeather API key found. Create a `.env` file in the project root "
        "with `OPENWEATHER_API_KEY=<your key>` (see `.env.example`), then restart the app."
    )
    st.stop()

if not city_choice or not city_choice.strip():
    st.info("Pick a city above to see its weather.")
    st.stop()

city = to_query(city_choice)

try:
    current_raw, forecast_raw = load_weather(city, units)
except WeatherAPIError as err:
    st.error(err.message)
    if err.kind in ("timeout", "connection", "server_error", "rate_limited"):
        st.info("This looks temporary. Wait a moment and search again.")
    st.stop()

current = extract_current_weather(current_raw, units)

theme_slot.markdown(
    theme_css(background_gradient(current["condition"], current["is_night"])) + banner_html(),
    unsafe_allow_html=True,
)

st.markdown(f"## {current['location']}")
st.markdown(f"<div class='temp-hero'>{current['temperature_display']}</div>", unsafe_allow_html=True)
st.markdown(f"**{current['description']}**")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Feels like", current["feels_like_display"])
col2.metric("Humidity", current["humidity_display"])
col3.metric("Wind", current["wind_speed_display"])
col4.metric("Pressure", current["pressure_display"])

col5, col6 = st.columns(2)
col5.metric("Sunrise", current["sunrise"])
col6.metric("Sunset", current["sunset"])

st.divider()
st.markdown("### Forecast")

intervals = extract_forecast_intervals(forecast_raw, units)
if intervals.empty:
    st.info("No forecast data available for this city.")
else:
    st.markdown("#### Daily summary")
    summary = daily_summary(intervals)
    day_cols = st.columns(max(len(summary), 1))
    for col, (_, row) in zip(day_cols, summary.iterrows()):
        with col, st.container(border=True):
            st.markdown(f"**{row['date']:%a %d %b}**")
            high = "N/A" if row["max_temp"] is None else f"{row['max_temp']:.0f}°"
            low = "N/A" if row["min_temp"] is None else f"{row['min_temp']:.0f}°"
            st.write(f"High {high} / Low {low}")
            st.caption(row["condition"] if row["condition"] != NA else "No condition data")

    st.markdown("#### Temperature every 3 hours")
    fig = px.line(
        intervals,
        x="time",
        y="temperature",
        markers=True,
        labels={"time": "Local time", "temperature": "Temperature (°C)"},
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Hourly forecast table"):
        st.dataframe(
            intervals[["time", "temperature", "feels_like", "humidity", "wind_speed", "description"]],
            use_container_width=True,
            hide_index=True,
        )
