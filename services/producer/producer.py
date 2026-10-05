import json
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "transactions.raw"

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
        return

    print(
        f"Message delivered to "
        f"{msg.topic()} [{msg.partition()}] "
        f"at offset {msg.offset()}"
    )


def create_transaction():
    return {
        "event_id": str(uuid.uuid4()),
        "customer_id": "C001",
        "amount": 550.50,
        "currency": "SIR",
        "transaction_type": "RETURN",
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
    }

def create_valid_transaction():
    return {
        "event_id": str(uuid.uuid4()),
        "customer_id": "C001",
        "amount": 125.50,
        "currency": "USD",
        "transaction_type": "PURCHASE",
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def create_null_customer_transaction():
    event = create_valid_transaction()
    event["customer_id"] = None
    return event


def create_invalid_amount_transaction():
    event = create_valid_transaction()
    event["amount"] = -250.00
    return event


def create_invalid_currency_transaction():
    event = create_valid_transaction()
    event["currency"] = "XYZ"
    return event


def create_invalid_transaction_type():
    event = create_valid_transaction()
    event["transaction_type"] = "CHARGEBACK"
    return event


def create_malformed_timestamp_transaction():
    event = create_valid_transaction()
    event["event_timestamp"] = "not-a-valid-timestamp"
    return event

SCENARIOS = {
    "valid": create_valid_transaction,
    "null_customer": create_null_customer_transaction,
    "invalid_amount": create_invalid_amount_transaction,
    "invalid_currency": create_invalid_currency_transaction,
    "invalid_transaction_type": create_invalid_transaction_type,
    "malformed_timestamp": create_malformed_timestamp_transaction,
}

def main():
    producer = Producer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        }
    )

    scenario = "malformed_timestamp"

    event = SCENARIOS[scenario]()

    producer.produce(
        topic=KAFKA_TOPIC,
        key=event["customer_id"] or event["event_id"],
        value=json.dumps(event),
        callback=delivery_report,
    )

    producer.flush()


if __name__ == "__main__":
    main()