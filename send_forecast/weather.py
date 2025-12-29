import logging
import requests
from datetime import datetime
import constants


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def format_day_label(date_str: str, index: int) -> str:
    if index == 0:
        return "Today"
    if index == 1:
        return "Tomorrow"

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%A")


def normalize_daily_forecast(daily: dict) -> list[dict]:
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
                "label": format_day_label(dates[i], i),
                "description": constants.WEATHER_CODE_MAP.get(
                    codes[i], "Unknown Weather Code"
                ),
            }
        )

    return forecast


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
                "label": format_day_label(dates[i], i),
                "description": constants.WEATHER_CODE_MAP.get(
                    codes[i], "Unknown Weather Code"
                ),
            }
        )

    return forecast


def fetch_multi_city_weather(cities):
    lats = ",".join(str(city.get("lat")) for city in cities)
    lons = ",".join(str(city.get("lon")) for city in cities)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lats,
        "longitude": lons,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Expected list response from weather API")

    return data


def build_forecast_payload(cities: list[dict]):
    """
        Build a forecast payload for a list of cities.

        :param cities: Subscriber cities
        :type cities: list[dict]
        :example: [{"city": "Charlotte", "state": "NC", "lat": 35.22709, "lon": -80.84313}]

        :return: Forecast payload
        :rtype: list[dict]
        :example: [
        {
            "city": "Charlotte",
            "state": "NC",
            "country": "US",
            "forecast": [
                {
                    "date": "2025-12-29",
                    "high": 61.9,
                    "low": 53.4,
                    "code": 3,
                },
                ...
            ],
        },
        {
            "city": "Huntersville",
            "state": "NC",
            "country": "US",
            "forecast": [...],
        },
    ]
    """

    if not cities:
        return []

    payload = []
    try:
        weather_data = fetch_multi_city_weather(cities)
    except Exception as e:
        logger.exception(f"Failed to fetch multi-city weather: {e}")
        for city in cities:
            try:
                forecast = fetch_weather(city["lat"], city["lon"])
                payload.append(
                    {
                        "city": city.get("city"),
                        "state": city.get("state"),
                        "forecast": forecast,
                    }
                )
            except Exception as e:
                payload.append(
                    {
                        "city": city.get("city"),
                        "state": city.get("state"),
                        "forecast": [],
                    }
                )
        return payload

    for idx, result in enumerate(weather_data):
        city = cities[idx]
        try:
            daily = result.get("daily", {})
            normalized_forecast = normalize_daily_forecast(daily)
            payload.append(
                {
                    "city": city.get("city"),
                    "state": city.get("state"),
                    "forecast": normalized_forecast,
                }
            )
        except Exception as e:
            logger.exception(
                f"Failed to normalize weather for {city.get('city')}, {city.get('state')}"
            )
            payload.append(
                {
                    "city": city.get("city"),
                    "state": city.get("state"),
                    "forecast": None,
                }
            )

    return payload
