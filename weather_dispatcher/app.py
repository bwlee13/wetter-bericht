import json
import logging
import os
from datetime import datetime
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


sns = boto3.client("sns")
dynamodb = boto3.client("dynamodb")

SNS_TOPIC_ARN = os.environ["WEATHER_FANOUT_TOPIC"]
DYNAMO_TABLE = os.environ["DYNAMO_TABLE_NAME"]


def deserialize_item(item):
    return {k: list(v.values())[0] for k, v in item.items()}


def get_all_subscribers():
    subscribers = []
    last_evaluated_key = None

    while True:
        params = {
            "TableName": DYNAMO_TABLE,
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": {"S": "PROFILE"}},
        }

        if last_evaluated_key:
            params["ExclusiveStartKey"] = last_evaluated_key

        response = dynamodb.query(**params)

        for item in response.get("Items", []):
            user = deserialize_item(item)
            print("USER FOUND: ", user.get("email", "NO EMAIL"))
            print("USER ACTIVE?: ", user.get("isActive", "isActive NOT FOUND"))
            if user.get("isActive", False):
                subscribers.append(user["email"])

        last_evaluated_key = response.get("LastEvaluatedKey")

        if not last_evaluated_key:
            break

    return subscribers


def lambda_handler(event, context):
    logger.info("WeatherDispatcherFunction invoked")

    subscribers = get_all_subscribers()
    logger.info("Found %d subscribers", len(subscribers))
    print("SUBSCRIBERS: ", subscribers)

    published = 0

    for email in subscribers:
        try:
            message = {
                "email": email,
                "runDate": datetime.strftime(datetime.now(), "%Y-%m-%d"),
            }
            print("MESSAGE: ", message)

            # sns.publish(
            #     TopicArn=SNS_TOPIC_ARN,
            #     Message=json.dumps(message),
            # )

            published += 1
            print("PUBLISHED COUNT: ", published)

            logger.info("Dispatched %d jobs to SNS", published)
        except Exception:
            logger.exception("Failed to dispatch weather job for %s", email)

    return {
        "statusCode": 200,
        "body": json.dumps({"subscribers": published, "status": "dispatched"}),
    }
