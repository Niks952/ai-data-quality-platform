import os
from typing import Any

import psycopg


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dq_user:dq_password@localhost:5432/data_quality",
)


def get_connection():
    return psycopg.connect(DATABASE_URL)


def save_dq_results(
    event: dict[str, Any],
    dataset_name: str,
    validation_errors: list[dict[str, Any]],
    source_topic: str,
    source_partition: int,
    source_offset: int,
) -> None:

    if not validation_errors:
        return

    query = """
        INSERT INTO dq_results (
            event_id,
            dataset_name,
            rule_id,
            rule_type,
            column_name,
            failure_message,
            source_topic,
            source_partition,
            source_offset
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    rows = []

    for error in validation_errors:

        rows.append(
            (
                event.get("event_id"),
                dataset_name,
                error.get("rule_id"),
                error.get("rule"),
                error.get("field"),
                error.get("message"),
                source_topic,
                source_partition,
                source_offset,
            )
        )

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.executemany(query, rows)

        connection.commit()