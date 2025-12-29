import json
import logging
import dynamo
import ses
import weather


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("SendForecastFunction invoked via SNS")
    try:
        sns_record = event["Records"][0]["Sns"]
        sns_message = json.loads(sns_record["Message"])
        logger.info(f"SNS Message: {sns_message}")

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error("Invalid SNS event format: %s", e)
        return {"statusCode": 400}

    email = sns_message.get("email")
    run_dt = sns_message.get("runDate")

    if not email:
        logger.error("SNS message missing 'email' field")
        return {"statusCode": 400}

    logger.info(f"Processing forecast for {email} | runDate={run_dt}")

    cities = dynamo.get_cities_for_subscriber(email)
    logger.info(f"Subscriber {email} has {len(cities)} cities")
    forecast_payload = weather.build_forecast_payload(cities)

    body = ses.build_email_body(forecast_payload)
    ses.send_email_to_subscriber(email, body)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "subscriber": email,
                "citiesCount": len(cities),
                "status": "sent",
            }
        ),
    }
