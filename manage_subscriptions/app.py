import json
import sys


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "manage subs",
                "body": sys.version,
            }
        ),
    }
