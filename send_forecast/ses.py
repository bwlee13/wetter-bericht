import logging
import boto3
import constants
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client("ses")


def build_email_body(forecast_payload: list[dict]) -> str:
    today_str = datetime.now().strftime("%A, %B %d, %Y")
    lines = [
        "Good morning!",
        f"Today is {today_str}",
        "",
        "🌤 Here is your daily detailed forecast:",
        "",
    ]

    if not forecast_payload:
        lines.append("- (No locations configured)")
    else:
        for city in forecast_payload:
            lines.append(f"- {city.get('city')}, {city.get('state')}")
            try:
                forecast = city.get("forecast", [])
                for day in forecast:
                    lines.append(
                        f"  {day['label']} {day['high']}°F / {day['low']}°F ({day['description']})"
                    )
            except Exception as e:
                logger.exception(
                    f"Failed to fetch weather for {city.get('city')}, {city.get('state')}",
                    f"Err: {e}",
                )
                lines.append("  (Weather unavailable)")

            lines.append("")

    # FOOTER
    footer = [
        "------------------------------",
        "Manage your subscriptions",
        "------------------------------",
        "",
        "Send an email to:",
        "weather@inbound.geistdevelopment.com",
        "",
        "One command per line in the body:",
        "ADD Charlotte, NC",
        "REMOVE Raleigh, NC",
        "LIST",
        "",
        "------------------------------",
        "",
        "— Wetter Bericht ☀️",
        "",
        "This is an automated email. Do not reply.",
    ]
    lines.extend(footer)

    return "\n".join(lines)


def send_email_to_subscriber(email: str, body: str):
    sender = constants.SENDER_EMAIL
    logger.info(f"Sending forecast email to {email}")

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
