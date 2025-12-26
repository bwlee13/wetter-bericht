import boto3
import os
import logging
from datetime import datetime
from boto3.dynamodb.types import TypeDeserializer

logger = logging.getLogger(__name__)

dynamodb = boto3.client("dynamodb")
DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE_NAME")


def deserialize_item(item):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in item.items()}


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
        Key={"PK": {"S": "PROFILE"}, "SK": {"S": f"PROFILE#{email}"}},
    )
    print("RESPONSE: ", response)
    return "Item" in response


def create_user(email: str):
    dynamodb.put_item(
        TableName=DYNAMO_TABLE,
        Item={
            "PK": {"S": "PROFILE"},
            "SK": {"S": f"PROFILE#{email}"},
            "email": {"S": email},
            "createdAt": {"S": datetime.now().isoformat()},
        },
        ConditionExpression="attribute_not_exists(PK)",
    )
    return


def add_city(email, payload, lat, lon):
    try:
        city, state = [x.strip() for x in payload.split(",")]
    except ValueError:
        logger.error(f"Invalid ADD payload: {payload}")
        return None, None

    item = {
        "PK": {"S": f"SUBSCRIPTION#{email}"},
        "SK": {"S": f"SUB#US#{state.upper()}#{city.upper()}"},
        "city": {"S": city},
        "state": {"S": state},
        "lat": {"N": str(lat)},
        "lon": {"N": str(lon)},
        "country": {"S": "US"},
        "createdAt": {"S": datetime.now().isoformat()},
    }

    dynamodb.put_item(TableName=DYNAMO_TABLE, Item=item)

    logger.info(f"Added city {city}, {state} for {email}")
    return city, state


def remove_city(email, payload):
    try:
        city, state = [x.strip() for x in payload.split(",")]
    except ValueError:
        logger.error(f"Invalid REMOVE payload: {payload}")
        return None, None

    dynamodb.delete_item(
        TableName=DYNAMO_TABLE,
        Key={
            "PK": {"S": f"SUBSCRIPTION#{email}"},
            "SK": {"S": f"SUB#CITY#US#{state.upper()}#{city.upper()}"},
        },
    )

    logger.info(f"Removed city {city}, {state} for {email}")
    return city, state


def list_cities(email):
    response = dynamodb.query(
        TableName=DYNAMO_TABLE,
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": {"S": f"SUBSCRIPTION#{email}"}},
    )

    items = response.get("Items", [])
    city_list = []
    for item in items:
        deserialized = deserialize_item(item)
        city_list.append(
            {
                "city": deserialized["city"],
                "state": deserialized["state"],
                "lat": float(deserialized["lat"]),
                "lon": float(deserialized["lon"]),
            }
        )

    print(f"Current subscriptions for {email}: {city_list}")
    return city_list
