import logging
import boto3
import os
from boto3.dynamodb.types import TypeDeserializer


logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
