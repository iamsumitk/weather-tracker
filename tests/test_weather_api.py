from unittest.mock import MagicMock

import pytest
import requests

from src.weather_api import WeatherAPIError, get_current_weather, get_forecast


def fake_response(status=200, payload=None, json_error=False):
    response = MagicMock()
    response.status_code = status
    if json_error:
        response.json.side_effect = ValueError("bad json")
    else:
        response.json.return_value = payload if payload is not None else {"name": "Berlin"}
    return response


def fake_session(response=None, exc=None):
    session = MagicMock(spec=requests.Session)
    if exc is not None:
        session.get.side_effect = exc
    else:
        session.get.return_value = response
    return session


def test_successful_request_returns_json_and_sends_params():
    session = fake_session(fake_response(200, {"name": "Berlin"}))
    data = get_current_weather("Berlin", "metric", api_key="KEY", session=session)
    assert data == {"name": "Berlin"}
    _, kwargs = session.get.call_args
    assert kwargs["params"] == {"q": "Berlin", "appid": "KEY", "units": "metric"}
    assert kwargs["timeout"] > 0


def test_forecast_uses_forecast_endpoint():
    session = fake_session(fake_response(200, {"list": []}))
    get_forecast("Berlin", "imperial", api_key="KEY", session=session)
    url = session.get.call_args[0][0]
    assert url.endswith("/data/2.5/forecast")


@pytest.mark.parametrize("status, kind", [
    (401, "invalid_key"),
    (404, "city_not_found"),
    (429, "rate_limited"),
    (500, "server_error"),
    (503, "server_error"),
    (418, "bad_response"),
])
def test_http_errors_map_to_error_kinds(status, kind):
    session = fake_session(fake_response(status))
    with pytest.raises(WeatherAPIError) as exc_info:
        get_current_weather("Berlin", api_key="KEY", session=session)
    assert exc_info.value.kind == kind


def test_timeout_is_reported():
    session = fake_session(exc=requests.exceptions.Timeout())
    with pytest.raises(WeatherAPIError) as exc_info:
        get_current_weather("Berlin", api_key="KEY", session=session)
    assert exc_info.value.kind == "timeout"


def test_connection_error_is_reported():
    session = fake_session(exc=requests.exceptions.ConnectionError())
    with pytest.raises(WeatherAPIError) as exc_info:
        get_current_weather("Berlin", api_key="KEY", session=session)
    assert exc_info.value.kind == "connection"


def test_invalid_json_is_reported():
    session = fake_session(fake_response(200, json_error=True))
    with pytest.raises(WeatherAPIError) as exc_info:
        get_current_weather("Berlin", api_key="KEY", session=session)
    assert exc_info.value.kind == "bad_response"


def test_missing_api_key_is_reported(monkeypatch):
    monkeypatch.setattr("src.config.OPENWEATHER_API_KEY", "")
    with pytest.raises(WeatherAPIError) as exc_info:
        get_current_weather("Berlin", api_key=None, session=fake_session(fake_response()))
    assert exc_info.value.kind == "missing_key"


def test_empty_city_is_rejected_without_calling_api():
    session = fake_session(fake_response())
    with pytest.raises(WeatherAPIError) as exc_info:
        get_current_weather("   ", api_key="KEY", session=session)
    assert exc_info.value.kind == "invalid_input"
    session.get.assert_not_called()


def test_unknown_units_are_rejected():
    with pytest.raises(WeatherAPIError) as exc_info:
        get_current_weather("Berlin", units="kelvin", api_key="KEY", session=fake_session(fake_response()))
    assert exc_info.value.kind == "invalid_input"
