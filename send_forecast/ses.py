import logging
import boto3
import weather
import constants
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client("ses")


def build_email_body(email: str, cities: list[dict]) -> str:
    today_str = datetime.now().strftime("%A, %B %d, %Y")
    lines = [
        "Good morning!",
        f"Today is {today_str}",
        "",
        "Here is your daily forecast:",
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
                forecast = weather.fetch_weather(city["lat"], city["lon"])
                for idx, day in enumerate(forecast):
                    label = weather.format_day_label(day["date"], idx)
                    description = constants.WEATHER_CODE_MAP.get(
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
    sender = constants.SENDER_EMAIL

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
