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
        "amount": 125.50,
        "currency": "USD",
        "transaction_type": "PURCHASE",
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    producer = Producer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        }
    )

    event = create_transaction()

    producer.produce(
        topic=KAFKA_TOPIC,
        key=event["customer_id"],
        value=json.dumps(event),
        callback=delivery_report,
    )

    producer.flush()


if __name__ == "__main__":
    main()