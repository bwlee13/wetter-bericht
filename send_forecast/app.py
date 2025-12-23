import json
import logging
import boto3
import os
from boto3.dynamodb.types import TypeDeserializer


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client("ses")

dynamodb = boto3.client("dynamodb")
TABLE_NAME = os.environ["DYNAMO_TABLE_NAME"]


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

    lines.extend(
        [
            "",
            "Weather details will be included here soon.",
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


def lambda_handler(event, context):
    logger.info("SendForecastFunction invoked")

    subscribers = get_all_subscribers()
    logger.info("Found %d subscribers", len(subscribers))

    for email in subscribers:
        cities = get_cities_for_subscriber(email)
        logger.info("Subscriber %s has %d cities", email, len(cities))

        body = build_email_body(email, cities)
        send_email_to_subscriber(email, body)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "subscribers": len(subscribers),
                "status": "emails sent",
            }
        ),
    }
