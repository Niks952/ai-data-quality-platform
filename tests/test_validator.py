from services.dq.validator import validate_transaction


def test_valid_transaction():

    event = {
        "event_id": "evt-001",
        "customer_id": "C001",
        "amount": 125.50,
        "currency": "USD",
        "transaction_type": "PURCHASE",
        "event_timestamp": "2026-10-04T12:30:00Z",
    }

    errors = validate_transaction(event)

    assert errors == []


def test_negative_amount():

    event = {
        "event_id": "evt-002",
        "customer_id": "C001",
        "amount": -50,
        "currency": "USD",
        "transaction_type": "PURCHASE",
        "event_timestamp": "2026-10-04T12:30:00Z",
    }

    errors = validate_transaction(event)

    assert any(
        error["rule"] == "POSITIVE_AMOUNT"
        for error in errors
    )


def test_missing_customer_id():

    event = {
        "event_id": "evt-003",
        "amount": 100,
        "currency": "USD",
        "transaction_type": "PURCHASE",
        "event_timestamp": "2026-10-04T12:30:00Z",
    }

    errors = validate_transaction(event)

    assert any(
        error["rule"] == "REQUIRED_FIELD"
        and error["field"] == "customer_id"
        for error in errors
    )