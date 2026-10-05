from typing import Any
from datetime import datetime


def validate_transaction(
    event: dict[str, Any],
    rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Validate an event using rules loaded from PostgreSQL.

    Returns a list of validation errors.
    An empty list means the event is valid.
    """

    errors = []

    for rule in rules:

        if not rule["enabled"]:
            continue

        rule_id = rule["rule_id"]
        rule_type = rule["rule_type"]
        column_name = rule["column_name"]
        rule_config = rule["rule_config"]

        value = event.get(column_name)

        if rule_type == "NOT_NULL":

            if column_name not in event or value is None:

                errors.append(
                    {
                        "rule_id": rule_id,
                        "rule": rule_type,
                        "field": column_name,
                        "message": (
                            f"Field cannot be null: {column_name}"
                        ),
                    }
                )

        elif rule_type == "RANGE":

            if value is None:
                continue

            minimum = rule_config.get("min")
            maximum = rule_config.get("max")

            if minimum is not None and value < minimum:

                errors.append(
                    {
                        "rule_id": rule_id,
                        "rule": rule_type,
                        "field": column_name,
                        "message": (
                            f"{column_name} must be greater than "
                            f"or equal to {minimum}"
                        ),
                    }
                )

            if maximum is not None and value > maximum:

                errors.append(
                    {
                        "rule_id": rule_id,
                        "rule": rule_type,
                        "field": column_name,
                        "message": (
                            f"{column_name} must be less than "
                            f"or equal to {maximum}"
                        ),
                    }
                )
        
        elif rule_type == "DATETIME":
            
            if value is None:
                continue

            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                errors.append(
                    {
                        "rule_id": rule_id,
                        "rule": rule_type,
                        "field": column_name,
                        "message": (
                            f"Invalid datetime value for "
                            f"{column_name}: {value}"
                        ),
                    }
                )

        elif rule_type == "ENUM":

            if value is None:
                continue

            allowed_values = rule_config.get("allowed", [])

            if value not in allowed_values:

                errors.append(
                    {
                        "rule_id": rule_id,
                        "rule": rule_type,
                        "field": column_name,
                        "message": (
                            f"Invalid value for {column_name}: {value}. "
                            f"Allowed values: {allowed_values}"
                        ),
                    }
                )

        else:

            errors.append(
                {
                    "rule_id": rule_id,
                    "rule": "UNKNOWN_RULE",
                    "field": column_name,
                    "message": (
                        f"Unsupported rule type: {rule_type}"
                    ),
                }
            )

    return errors