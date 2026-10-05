import os
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dq_user:dq_password@localhost:5432/data_quality",
)


def get_connection():
    return psycopg.connect(DATABASE_URL)


def save_insight(
    dataset_name: str,
    total_failures: int,
    failed_events: int,
    insight: dict[str, Any],
    model_name: str,
) -> None:

    query = """
        INSERT INTO ai_insights (
            dataset_name,
            total_failures,
            failed_events,
            insight,
            model_name
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    dataset_name,
                    total_failures,
                    failed_events,
                    Jsonb(insight),
                    model_name,
                ),
            )

        connection.commit()