from client.weather_client import get_current_weather, get_weather_history, get_full_weather

def test_get_current_weather_returns_dict():
    result = get_current_weather("Iasi")
    assert isinstance(result, dict)
    assert "temperature" in result
    assert "humidity" in result


def test_get_current_weather_invalid_city():
    result = get_current_weather("FakeCityXYZ")
    assert "error" in result


def test_get_weather_history_returns_list():
    history = get_weather_history("Iasi", limit=5)
    assert isinstance(history, list)


def test_get_full_weather_combines_data():
    full = get_full_weather("Iasi")
    assert "current" in full and "history" in full
