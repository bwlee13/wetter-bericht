import json
import logging
import dynamo
import ses


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("SendForecastFunction invoked")

    subscribers = dynamo.get_all_subscribers()
    logger.info("Found %d subscribers", len(subscribers))

    for email in subscribers:
        cities = dynamo.get_cities_for_subscriber(email)
        logger.info("Subscriber %s has %d cities", email, len(cities))

        body = ses.build_email_body(email, cities)
        print("Email body for %s:\n%s", email, body)
        ses.send_email_to_subscriber(email, body)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "subscribers": len(subscribers),
                "status": "emails sent",
            }
        ),
    }
