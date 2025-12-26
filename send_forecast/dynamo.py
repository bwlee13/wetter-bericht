import logging
import boto3
import os
from boto3.dynamodb.types import TypeDeserializer

logger = logging.getLogger(__name__)

dynamodb = boto3.client("dynamodb")
TABLE_NAME = os.environ["DYNAMO_TABLE_NAME"]


def deserialize_item(item):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in item.items()}


def get_all_subscribers():
    response = dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": {"S": "PROFILE"}},
    )
    items = response.get("Items", [])
    return [deserialize_item(item)["email"] for item in items]


def get_cities_for_subscriber(email: str):
    response = dynamodb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={
            ":pk": {"S": f"SUBSCRIPTION#{email}"},
            ":sk": {"S": "SUB#"},
        },
    )
    items = response.get("Items", [])
    return [deserialize_item(item) for item in items]
