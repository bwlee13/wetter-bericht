import logging
import requests
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def format_day_label(date_str: str, index: int) -> str:
    if index == 0:
        return "Today"
    if index == 1:
        return "Tomorrow"

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%A")


def fetch_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    codes = daily.get("weathercode", [])

    forecast = []
    for i in range(min(7, len(dates))):
        forecast.append(
            {
                "date": dates[i],
                "high": highs[i],
                "low": lows[i],
                "code": codes[i],
            }
        )

    return forecast
