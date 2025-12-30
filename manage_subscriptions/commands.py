import dynamo
import logging
import geocode

logger = logging.getLogger(__name__)


def parse_commands(body):
    commands = []

    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split(" ", 1)
        command = parts[0].upper()

        payload = parts[1].strip() if len(parts) > 1 else ""

        if command in {"ADD", "REMOVE", "LIST"}:
            commands.append((command, payload))

    return commands


def execute_commands(sender_email: str, commands: list[tuple[str, str]]):
    """
    Executes parsed commands for a sender.
    Ensures user exists before executing commands.
    Returns structured results for response email.
    """

    results = {"added": [], "removed": [], "listed": None, "errors": []}

    if not commands:
        results["errors"].append({"error": "No valid commands found"})
        return results

    # Ensure user exists
    user_created = dynamo.get_or_create_user(sender_email)

    if user_created:
        logger.info(f"Created new subscriber profile for {sender_email}")
    else:
        logger.info(f"Subscriber profile exists for {sender_email}")

    # Execute commands
    for command, payload in commands:
        try:
            if command == "ADD":
                lat, lon = geocode.resolve_city(payload)
                city, state = dynamo.add_city(sender_email, payload, lat, lon)
                if city and state:
                    results["added"].append({"city": city, "state": state})

            elif command == "REMOVE":
                city, state = dynamo.remove_city(sender_email, payload)
                if city and state:
                    results["removed"].append({"city": city, "state": state})

            elif command == "LIST":
                cities = dynamo.list_cities(sender_email)
                results["listed"] = cities

        except Exception as e:
            logger.exception("Failed executing command")
            results["errors"].append(
                {"command": command, "payload": payload, "error": str(e)}
            )

    return results
