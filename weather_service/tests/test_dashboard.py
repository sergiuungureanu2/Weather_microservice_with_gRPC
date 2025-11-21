import pytest
import plotly.express as px
from datetime import datetime
from frontend.dashboard import update_dashboard

def test_plot_with_valid_data(monkeypatch):
    city = "Iasi"
    n_clicks, n_intervals = 0, 0
    monkeypatch.setattr("client.weather_client.get_current_weather", lambda c: {
        "city": city, "country": "RO", "temperature": 10, "humidity": 80,
        "wind_speed": 5, "description": "clear", "api_timestamp": 1732000000, "request_timestamp": 1732000050
    })
    mock_history = [
        {"datetime": datetime.utcnow(), "temperature": 10, "humidity": 80},
        {"datetime": datetime.utcnow(), "temperature": 9, "humidity": 82},
    ]
    monkeypatch.setattr("client.weather_client.get_weather_history", lambda c, limit=50: mock_history)

    current, temp_fig, hum_fig, _ = update_dashboard(n_intervals, n_clicks, city)
    assert "Weather in" in current.children[0].children
    assert isinstance(temp_fig, type(px.line()))
    assert isinstance(hum_fig, type(px.line()))
