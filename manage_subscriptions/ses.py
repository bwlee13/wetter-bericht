from email import policy
from email.parser import BytesParser
import re
import logging
from dataclasses import dataclass
import boto3
import weather
import constants

logger = logging.getLogger(__name__)

SENDER_EMAIL = "brandon@geistdevelopment.com"
ses = boto3.client("ses")


@dataclass(frozen=True, slots=True)
class EmailData:
    sender_email: str
    subject: str
    body: str
    statusCode: int = 200


def parse_ses_event(ses_event: dict) -> EmailData:
    """
    Extracts relevant information from an SES event dictionary.

    Args:
        ses_event (dict): The SES event payload.

    Returns:
        EmailData: An instance of EmailData containing the sender, subject, and body of the email.

        class EmailData:
            sender_email: str
            subject: str
            body: str
            statusCode: int = 200
    """

    if "content" not in ses_event:
        logger.error("SES event does not contain email content")
        return EmailData(sender_email="", subject="", body="", statusCode=400)

    msg_from = ses_event["mail"]["source"]
    sender_email = extract_email_address(msg_from)

    raw_email = ses_event["content"].encode("utf-8")
    subject, body = parse_email(raw_email)

    return EmailData(
        sender_email=sender_email,
        subject=subject,
        body=body,
    )


def parse_email(raw_bytes):
    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)

    subject = msg["Subject"]

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content()

    return subject, body


def extract_email_address(from_header):
    match = re.search(r"<(.+?)>", from_header)
    return match.group(1) if match else from_header.strip()


def exec_send_email(email: str, subject: str, body: str):
    sender = SENDER_EMAIL

    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {
                "Charset": "UTF-8",
                "Data": subject,
            },
            "Body": {
                "Text": {
                    "Charset": "UTF-8",
                    "Data": body,
                }
            },
        },
    )


def send_resp_email(results: dict, to_email: str):
    """
    Builds and sends a subscription response email based on command execution results.
    """

    lines = []
    lines.append("Hello, here are the results of your subscription commands:")
    lines.append("")

    # ADD RESULTS
    if results["added"]:
        lines.append("✅ Added the following subscriptions:")
        for item in results["added"]:
            lines.append(f"  - {item['city']}, {item['state']}")
        lines.append("")

    # REMOVE RESULTS
    if results["removed"]:
        lines.append("❌ Removed the following subscriptions:")
        for item in results["removed"]:
            lines.append(f"  - {item['city']}, {item['state']}")
        lines.append("")

    # LIST + WEATHER
    if results["listed"] is not None:
        lines.append("📍 You are currently subscribed to the following locations:")
        for item in results["listed"]:
            lines.append(f"  - {item['city']}, {item['state']}")
        lines.append("")

        lines.append("🌤 Detailed Forecast:")
        lines.append("")

        for sub in results["listed"]:
            forecast = weather.fetch_weather(
                lat=sub["lat"],
                lon=sub["lon"],
            )

            lines.append(f"- {sub['city']}, {sub['state']} ")

            for idx, day in enumerate(forecast):
                label = weather.format_day_label(day["date"], idx)
                description = constants.WEATHER_CODE_MAP.get(
                    day["code"], "Unknown Weather Code"
                )
                lines.append(
                    f"  {label} {day['high']}°F / {day['low']}°F ({description})"
                )

            lines.append("")

    # ERRORS
    if results["errors"]:
        lines.append("⚠️ Some commands could not be processed:")
        for error in results["errors"]:
            lines.append(
                f"  - {error['command']} {error['payload']} — {error['error']}"
            )
        lines.append("")

    # FALLBACK
    if (
        not results["added"]
        and not results["removed"]
        and results["listed"] is None
        and not results["errors"]
    ):
        return

    # FOOTER
    lines.append(
        "To manage your subscriptions, send an email to weather@inbound.geistdevelopment.com with commands in the body like:"
    )
    lines.append("ADD Charlotte, NC")
    lines.append("REMOVE Raleigh, NC")
    lines.append("LIST")
    lines.append("")
    lines.append("— Wetter Bericht ☀️")

    body = "\n".join(lines)

    exec_send_email(
        email=to_email,
        subject="Your Wetter Bericht subscription update",
        body=body,
    )

    return "\n".join(lines)
