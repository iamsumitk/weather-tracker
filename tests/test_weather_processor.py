import pandas as pd

from src.weather_processor import (
    NA,
    daily_summary,
    extract_current_weather,
    extract_forecast_intervals,
    format_humidity,
    format_pressure,
    format_speed,
    format_temperature,
)

CURRENT_RESPONSE = {
    "name": "London",
    "sys": {"country": "GB", "sunrise": 1700000000, "sunset": 1700040000},
    "timezone": 0,
    "main": {"temp": 18.5, "feels_like": 17.8, "humidity": 65, "pressure": 1012},
    "weather": [{"description": "light rain", "main": "Rain"}],
    "wind": {"speed": 4.2},
}


def test_format_temperature_metric_and_imperial():
    assert format_temperature(18.5, "metric") == "18.5 °C"
    assert format_temperature(65.0, "imperial") == "65.0 °F"


def test_format_helpers_handle_none():
    assert format_temperature(None) == NA
    assert format_speed(None) == NA
    assert format_humidity(None) == NA
    assert format_pressure(None) == NA


def test_format_speed_and_others():
    assert format_speed(4.2, "metric") == "4.2 m/s"
    assert format_speed(4.2, "imperial") == "4.2 mph"
    assert format_humidity(65) == "65%"
    assert format_pressure(1012) == "1012 hPa"


def test_extract_current_weather_full_response():
    result = extract_current_weather(CURRENT_RESPONSE, "metric")
    assert result["location"] == "London, GB"
    assert result["temperature_display"] == "18.5 °C"
    assert result["feels_like_display"] == "17.8 °C"
    assert result["humidity_display"] == "65%"
    assert result["pressure_display"] == "1012 hPa"
    assert result["wind_speed_display"] == "4.2 m/s"
    assert result["description"] == "Light rain"
    assert result["condition"] == "Rain"


def test_extract_current_weather_missing_fields_fall_back_safely():
    result = extract_current_weather({}, "metric")
    assert result["location"] == "Unknown location"
    assert result["temperature_display"] == NA
    assert result["humidity_display"] == NA
    assert result["description"] == NA
    assert result["condition"] == NA
    assert result["sunrise"] == NA


def test_extract_current_weather_handles_null_and_empty_lists():
    data = {"name": "Oslo", "main": None, "weather": [], "wind": {"speed": None}}
    result = extract_current_weather(data, "metric")
    assert result["location"] == "Oslo"
    assert result["temperature_display"] == NA
    assert result["wind_speed_display"] == NA
    assert result["description"] == NA


def test_sunrise_is_converted_to_city_local_time():
    # 1700000000 is 2023-11-14 22:13:20 UTC; +3600 s offset -> 23:13
    data = {"sys": {"sunrise": 1700000000}, "timezone": 3600}
    assert extract_current_weather(data)["sunrise"] == "23:13"


def make_forecast(entries, tz=0):
    return {"city": {"timezone": tz}, "list": entries}


def entry(dt, temp, condition="Clouds"):
    return {
        "dt": dt,
        "main": {"temp": temp, "feels_like": temp - 1, "humidity": 70},
        "weather": [{"main": condition, "description": condition.lower()}],
        "wind": {"speed": 3.0},
    }


def test_forecast_intervals_are_converted_to_local_time():
    # 1700000000 UTC = 2023-11-14 22:13:20; offset +3600 -> 23:13:20
    data = make_forecast([entry(1700000000, 10.0)], tz=3600)
    df = extract_forecast_intervals(data)
    assert len(df) == 1
    assert df.iloc[0]["time"] == pd.Timestamp("2023-11-14 23:13:20")
    assert str(df.iloc[0]["date"]) == "2023-11-14"


def test_forecast_skips_entries_without_timestamp():
    data = make_forecast([{"main": {"temp": 5}}, entry(1700000000, 10.0)])
    assert len(extract_forecast_intervals(data)) == 1


def test_forecast_with_no_list_returns_empty_frame():
    df = extract_forecast_intervals({})
    assert df.empty
    assert "temperature" in df.columns


def test_daily_summary_groups_by_date_with_max_min_and_dominant_condition():
    # 1699920000 = 2023-11-14 00:00 UTC. Three entries on day 1 (Rain x2,
    # Clouds x1) at 00:00, 03:00, 06:00; one entry on day 2 at 00:00.
    data = make_forecast([
        entry(1699920000, 10.0, "Rain"),
        entry(1699930800, 14.0, "Rain"),
        entry(1699941600, 8.0, "Clouds"),
        entry(1700006400, 20.0, "Clear"),
    ])
    summary = daily_summary(extract_forecast_intervals(data))
    assert len(summary) == 2
    day1 = summary.iloc[0]
    assert day1["max_temp"] == 14.0
    assert day1["min_temp"] == 8.0
    assert day1["condition"] == "Rain"
    assert summary.iloc[1]["max_temp"] == 20.0


def test_daily_summary_of_empty_input_is_empty():
    summary = daily_summary(extract_forecast_intervals({}))
    assert summary.empty
    assert list(summary.columns) == ["date", "max_temp", "min_temp", "condition"]


def test_daily_summary_ignores_missing_temperatures():
    data = make_forecast([{"dt": 1700000000, "main": {}, "weather": []}])
    summary = daily_summary(extract_forecast_intervals(data))
    assert summary.iloc[0]["max_temp"] is None
    assert summary.iloc[0]["condition"] == NA


def test_current_weather_reports_day_or_night_from_icon():
    day = extract_current_weather({"weather": [{"main": "Clear", "icon": "01d"}]})
    night = extract_current_weather({"weather": [{"main": "Clear", "icon": "01n"}]})
    assert day["is_night"] is False
    assert night["is_night"] is True
    assert night["condition"] == "Clear"
