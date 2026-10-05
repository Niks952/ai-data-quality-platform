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

    rules = [
        {
            "rule_id": 1,
            "rule_type": "NOT_NULL",
            "column_name": "customer_id",
            "rule_config": {},
            "enabled": True,
        },
        {
            "rule_id": 2,
            "rule_type": "RANGE",
            "column_name": "amount",
            "rule_config": {"min": 0},
            "enabled": True,
        },
        {
            "rule_id": 3,
            "rule_type": "ENUM",
            "column_name": "currency",
            "rule_config": {
                "allowed": ["USD", "EUR", "GBP", "INR"]
            },
            "enabled": True,
        },
    ]

    errors = validate_transaction(event, rules)

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

    rules = [
        {
            "rule_id": 1,
            "rule_type": "RANGE",
            "column_name": "amount",
            "rule_config": {"min": 0},
            "enabled": True,
        },
    ]

    errors = validate_transaction(event, rules)

    assert any(
        error["rule"] == "RANGE"
        and error["field"] == "amount"
        for error in errors
    )


def test_invalid_currency():

    event = {
        "event_id": "evt-003",
        "customer_id": "C001",
        "amount": 100,
        "currency": "XYZ",
        "transaction_type": "PURCHASE",
        "event_timestamp": "2026-10-04T12:30:00Z",
    }

    rules = [
        {
            "rule_id": 1,
            "rule_type": "ENUM",
            "column_name": "currency",
            "rule_config": {
                "allowed": ["USD", "EUR", "GBP", "INR"]
            },
            "enabled": True,
        },
    ]

    errors = validate_transaction(event, rules)

    assert any(
        error["rule"] == "ENUM"
        and error["field"] == "currency"
        for error in errors
    )


def test_missing_customer_id():

    event = {
        "event_id": "evt-004",
        "amount": 100,
        "currency": "USD",
        "transaction_type": "PURCHASE",
        "event_timestamp": "2026-10-04T12:30:00Z",
    }

    rules = [
        {
            "rule_id": 1,
            "rule_type": "NOT_NULL",
            "column_name": "customer_id",
            "rule_config": {},
            "enabled": True,
        },
    ]

    errors = validate_transaction(event, rules)

    assert any(
        error["rule"] == "NOT_NULL"
        and error["field"] == "customer_id"
        for error in errors
    )