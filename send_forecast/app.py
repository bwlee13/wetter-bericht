import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("SendDailyForecast invoked")
    logger.info(f"Event: {json.dumps(event)}")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "SendDailyForecast function executed successfully",
            }
        ),
    }
