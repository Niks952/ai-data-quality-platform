from typing import Any


REQUIRED_FIELDS = {
    "event_id": str,
    "customer_id": str,
    "amount": (int, float),
    "currency": str,
    "transaction_type": str,
    "event_timestamp": str,
}


def validate_transaction(event: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Validate a transaction event.

    Returns a list of validation errors.
    An empty list means the event is valid.
    """

    errors = []

    # Schema / required field checks
    for field, expected_type in REQUIRED_FIELDS.items():

        if field not in event:
            errors.append(
                {
                    "rule": "REQUIRED_FIELD",
                    "field": field,
                    "message": f"Missing required field: {field}",
                }
            )
            continue

        value = event[field]

        if value is None:
            errors.append(
                {
                    "rule": "NULL_CHECK",
                    "field": field,
                    "message": f"Field cannot be null: {field}",
                }
            )
            continue

        if not isinstance(value, expected_type):
            errors.append(
                {
                    "rule": "DATA_TYPE",
                    "field": field,
                    "message": (
                        f"Invalid type for {field}. "
                        f"Expected {expected_type}, "
                        f"got {type(value).__name__}"
                    ),
                }
            )

    # Business rules
    if "amount" in event and isinstance(event["amount"], (int, float)):
        if event["amount"] <= 0:
            errors.append(
                {
                    "rule": "POSITIVE_AMOUNT",
                    "field": "amount",
                    "message": "Transaction amount must be greater than zero",
                }
            )

    if "currency" in event and event["currency"] is not None:
        allowed_currencies = {"USD", "EUR", "GBP", "INR"}

        if event["currency"] not in allowed_currencies:
            errors.append(
                {
                    "rule": "VALID_CURRENCY",
                    "field": "currency",
                    "message": f"Unsupported currency: {event['currency']}",
                }
            )

    if "transaction_type" in event and event["transaction_type"] is not None:
        allowed_types = {
            "PURCHASE",
            "REFUND",
            "TRANSFER",
        }

        if event["transaction_type"] not in allowed_types:
            errors.append(
                {
                    "rule": "VALID_TRANSACTION_TYPE",
                    "field": "transaction_type",
                    "message": (
                        f"Unsupported transaction type: "
                        f"{event['transaction_type']}"
                    ),
                }
            )

    return errors