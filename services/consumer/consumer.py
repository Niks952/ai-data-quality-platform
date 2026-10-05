import json

from confluent_kafka import Consumer, KafkaException, Producer

from services.dq.rule_repository import get_enabled_rules
from services.dq.validator import validate_transaction
from services.dq.result_repository import save_dq_results


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

INPUT_TOPIC = "transactions.raw"
VALIDATED_TOPIC = "transactions.validated"
DLQ_TOPIC = "transactions.dlq"

CONSUMER_GROUP = "dq-validation-consumer"


def create_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )


def create_producer() -> Producer:
    return Producer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        }
    )


def delivery_report(err, msg):

    if err is not None:
        print(f"Delivery failed: {err}")
        return

    print(
        f"Delivered to "
        f"{msg.topic()} "
        f"[{msg.partition()}] "
        f"offset={msg.offset()}"
    )


def main():

    consumer = create_consumer()
    producer = create_producer()

    consumer.subscribe([INPUT_TOPIC])

    rules = get_enabled_rules("transactions")

    print(f"Listening to {INPUT_TOPIC}")
    print(f"Loaded {len(rules)} DQ rules")

    try:

        while True:

            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            try:

                raw_value = msg.value().decode("utf-8")
                event = json.loads(raw_value)

            except (UnicodeDecodeError, json.JSONDecodeError) as error:

                dlq_event = {
                    "original_message": msg.value().decode(
                        "utf-8",
                        errors="replace",
                    ),
                    "error_type": "INVALID_JSON",
                    "error_message": str(error),
                    "source_topic": msg.topic(),
                    "source_partition": msg.partition(),
                    "source_offset": msg.offset(),
                }

                producer.produce(
                    topic=DLQ_TOPIC,
                    value=json.dumps(dlq_event),
                    callback=delivery_report,
                )

                producer.flush()

                consumer.commit(message=msg)

                continue

            errors = validate_transaction(event, rules)

            if errors:

                save_dq_results(
                    event=event,
                    dataset_name="transactions",
                    validation_errors=errors,
                    source_topic=msg.topic(),
                    source_partition=msg.partition(),
                    source_offset=msg.offset(),
                )

                dlq_event = {
                    "original_event": event,
                    "validation_errors": errors,
                    "source_topic": msg.topic(),
                    "source_partition": msg.partition(),
                    "source_offset": msg.offset(),
                }

                print(
                    f"Validation failed for "
                    f"{event.get('event_id')}: "
                    f"{errors}"
                )

                producer.produce(
                    topic=DLQ_TOPIC,
                    key=event.get("customer_id"),
                    value=json.dumps(dlq_event),
                    callback=delivery_report,
                )

            else:

                print(
                    f"Validation passed for "
                    f"{event['event_id']}"
                )

                producer.produce(
                    topic=VALIDATED_TOPIC,
                    key=event["customer_id"],
                    value=json.dumps(event),
                    callback=delivery_report,
                )

            producer.flush()

            consumer.commit(message=msg)

    except KeyboardInterrupt:

        print("\nConsumer stopped.")

    finally:

        consumer.close()


if __name__ == "__main__":
    main()