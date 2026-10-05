import json
import os

import psycopg


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dq_user:dq_password@localhost:5432/data_quality",
)


def get_connection():
    return psycopg.connect(DATABASE_URL)


def get_enabled_rules(dataset_name: str) -> list[dict]:
    query = """
        SELECT
            rule_id,
            dataset_name,
            rule_type,
            column_name,
            rule_config,
            enabled
        FROM dq_rules
        WHERE dataset_name = %s
          AND enabled = TRUE
        ORDER BY rule_id
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(query, (dataset_name,))

            rows = cursor.fetchall()

    rules = []

    for row in rows:

        rule_id = row[0]
        dataset_name = row[1]
        rule_type = row[2]
        column_name = row[3]
        rule_config = row[4]
        enabled = row[5]

        if isinstance(rule_config, str):
            rule_config = json.loads(rule_config)

        rules.append(
            {
                "rule_id": rule_id,
                "dataset_name": dataset_name,
                "rule_type": rule_type,
                "column_name": column_name,
                "rule_config": rule_config,
                "enabled": enabled,
            }
        )

    return rules