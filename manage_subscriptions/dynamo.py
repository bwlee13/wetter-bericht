import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

dynamodb = boto3.client("dynamodb")

DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE_NAME")


def get_or_create_user(email: str) -> bool:
    """
    Returns True if user was created, False if already existed.
    """
    if user_exists(email):
        return False

    create_user(email)
    return True


def user_exists(email: str) -> bool:
    response = dynamodb.get_item(
        TableName=DYNAMO_TABLE,
        Key={"PK": {"S": f"SUBSCRIBER#{email}"}, "SK": {"S": "PROFILE"}},
    )
    return "Item" in response


def create_user(email: str):
    dynamodb.put_item(
        TableName=DYNAMO_TABLE,
        Item={
            "PK": {"S": f"SUBSCRIBER#{email}"},
            "SK": {"S": "PROFILE"},
            "email": {"S": email},
            "createdAt": {"S": datetime.now().isoformat()},
        },
        ConditionExpression="attribute_not_exists(PK)",
    )


def add_city(email, payload):
    try:
        city, state = [x.strip() for x in payload.split(",")]
    except ValueError:
        logger.error(f"Invalid ADD payload: {payload}")
        return

    item = {
        "PK": {"S": f"SUBSCRIBER#{email}"},
        "SK": {"S": f"CITY#US#{state.upper()}#{city.upper()}"},
        "city": {"S": city},
        "state": {"S": state},
        "country": {"S": "US"},
    }

    dynamodb.put_item(TableName=DYNAMO_TABLE, Item=item)

    logger.info(f"Added city {city}, {state} for {email}")


def remove_city(email, payload):
    try:
        city, state = [x.strip() for x in payload.split(",")]
    except ValueError:
        logger.error(f"Invalid REMOVE payload: {payload}")
        return

    dynamodb.delete_item(
        TableName=DYNAMO_TABLE,
        Key={
            "PK": {"S": f"SUBSCRIBER#{email}"},
            "SK": {"S": f"CITY#US#{state.upper()}#{city.upper()}"},
        },
    )

    logger.info(f"Removed city {city}, {state} for {email}")


def list_cities(email):
    response = dynamodb.query(
        TableName=DYNAMO_TABLE,
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": {"S": f"SUBSCRIBER#{email}"}},
    )

    cities = response.get("Items", [])
    logger.info(f"Current subscriptions for {email}: {cities}")
    return cities
