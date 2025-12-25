from email import policy
from email.parser import BytesParser
import re
import logging

logger = logging.getLogger(__name__)


def parse_ses_event(ses_event: dict) -> dict:
    """
    Extracts relevant information from an SES event dictionary.

    Args:
        ses_event (dict): The SES event payload.

    Returns:
        dict: A dictionary containing the sender, subject, and body of the email.
    """
    if "content" not in ses_event:
        logger.error("SES event does not contain email content")
        return {"statusCode": 400}

    msg_from = ses_event["mail"]["source"]
    sender_email = extract_email_address(msg_from)

    logger.info("Email from: %s", msg_from)
    logger.info("Sender Email from: %s", sender_email)

    raw_email = ses_event["content"].encode("utf-8")
    sender, subject, body = parse_email(raw_email)

    return {
        "sender_email": sender,
        "subject": subject,
        "body": body,
    }


def parse_email(raw_bytes):
    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)

    sender = msg["From"]
    subject = msg["Subject"]

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content()

    return sender, subject, body


def extract_email_address(from_header):
    match = re.search(r"<(.+?)>", from_header)
    return match.group(1) if match else from_header.strip()
