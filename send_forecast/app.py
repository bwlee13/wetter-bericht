import json
import logging
import boto3
import os
from boto3.dynamodb.types import TypeDeserializer
import requests
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client("ses")

dynamodb = boto3.client("dynamodb")
TABLE_NAME = os.environ["DYNAMO_TABLE_NAME"]

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Heavy rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def deserialize_item(item):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in item.items()}


def get_all_subscribers():
    response = dynamodb.scan(
        TableName=TABLE_NAME,
        FilterExpression="SK = :sk",
        ExpressionAttributeValues={":sk": {"S": "PROFILE"}},
    )
    items = response.get("Items", [])
    return [deserialize_item(item)["email"] for item in items]


def get_cities_for_subscriber(email: str):
    response = dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={
            ":pk": {"S": f"SUBSCRIBER#{email}"},
            ":sk": {"S": "CITY#"},
        },
    )
    items = response.get("Items", [])
    return [deserialize_item(item) for item in items]


def build_email_body(email: str, cities: list[dict]) -> str:
    lines = [
        "Good morning!",
        "",
        "Here are your subscribed locations:",
        "",
    ]

    if not cities:
        lines.append("- (No locations configured)")
    else:
        for city in cities:
            lines.append(
                f"- {city.get('city')}, {city.get('state')} ({city.get('country')})"
            )
            try:
                forecast = fetch_weather(city["lat"], city["lon"])
                for idx, day in enumerate(forecast):
                    label = format_day_label(day["date"], idx)
                    description = WEATHER_CODE_MAP.get(
                        day["code"], "Unknown Weather Code"
                    )
                    lines.append(
                        f"  {label} {day['high']}°F / {day['low']}°F ({description})"
                    )
            except Exception as e:
                logger.exception(
                    "Err: f{e}",
                    "Failed to fetch weather for %s, %s",
                    city.get("city"),
                    city.get("state"),
                )
                lines.append("  (Weather unavailable)")

            lines.append("")

    lines.extend(
        [
            "",
            "— Wetter Bericht",
        ]
    )

    return "\n".join(lines)


def send_email_to_subscriber(email: str, body: str):
    sender = "brandon@geistdevelopment.com"

    logger.info("Sending forecast email to %s", email)

    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {
                "Charset": "UTF-8",
                "Data": "Wetter Bericht – Daily Forecast",
            },
            "Body": {
                "Text": {
                    "Charset": "UTF-8",
                    "Data": body,
                }
            },
        },
    )


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


def lambda_handler(event, context):
    logger.info("SendForecastFunction invoked")

    subscribers = get_all_subscribers()
    logger.info("Found %d subscribers", len(subscribers))

    for email in subscribers:
        cities = get_cities_for_subscriber(email)
        logger.info("Subscriber %s has %d cities", email, len(cities))

        body = build_email_body(email, cities)
        print("Email body for %s:\n%s", email, body)
        # send_email_to_subscriber(email, body)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "subscribers": len(subscribers),
                "status": "emails sent",
            }
        ),
    }
