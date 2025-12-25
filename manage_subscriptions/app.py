import json
import logging
import ses
import commands

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("ManageSubscriptionsFunction invoked")
    logger.info(event)

    # Unwrap SNS
    sns_record = event["Records"][0]["Sns"]
    ses_event = json.loads(sns_record["Message"])

    logger.info("Unwrapped Message from SES Mail Manager payload")

    # Extract Email Content
    email_content = ses.parse_ses_event(ses_event)

    sender_email = email_content["sender_email"]
    subject = email_content["subject"]
    body = email_content["body"]

    logger.info(
        "================ EMAIL RECEIVED ================\n"
        f"Sender : {sender_email}\n"
        f"Subject: {subject}\n"
        "------------------------------------------------\n"
        f"{body}\n"
        "================================================"
    )

    # Parse commands
    cmds = commands.parse_commands(body)
    logger.info(f"Parsed commands: {cmds}")

    results = commands.execute_commands(sender_email, cmds)
    logger.info(f"Command execution results: {results}")

    # # Execute commands
    # for command, payload in cmds:
    #     if command == "ADD":
    #         dynamo.add_city(sender_email, payload)
    #     elif command == "REMOVE":
    #         dynamo.remove_city(sender_email, payload)
    #     elif command == "LIST":
    #         dynamo.list_cities(sender_email)

    return {"statusCode": 200}
