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
    if email_content.statusCode != 200:
        logger.error("Failed to parse SES event")
        return {"statusCode": email_content.statusCode}

    # Parse commands
    cmds = commands.parse_commands(email_content.body)
    logger.info(f"Parsed commands: {cmds}")

    results = commands.execute_commands(email_content.sender_email, cmds)

    # Send response email
    ses.send_resp_email(results, email_content.sender_email)

    return {"statusCode": 200}
