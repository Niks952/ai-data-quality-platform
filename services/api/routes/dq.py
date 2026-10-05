from fastapi import APIRouter
import psycopg
import json

from services.ai.ollama_client import generate_insight
from services.ai.insight_repository import save_insight

router = APIRouter(prefix="/dq", tags=["Data Quality"])


DATABASE_URL = (
    "postgresql://dq_user:dq_password@localhost:5432/data_quality"
)

@router.get("/overview")
def get_overview():
    summary_query = """
        SELECT
            COUNT(*) AS total_failures,
            COUNT(DISTINCT event_id) AS failed_events,
            COUNT(DISTINCT rule_id) AS failing_rules
        FROM dq_results
    """

    results_query = """
        SELECT
            result_id,
            event_id,
            rule_type,
            column_name,
            failure_message,
            processed_at
        FROM dq_results
        ORDER BY processed_at DESC
        LIMIT 10
    """

    rules_query = """
        SELECT
            COUNT(*) FILTER (WHERE enabled = TRUE),
            COUNT(*) FILTER (WHERE enabled = FALSE)
        FROM dq_rules
    """

    insight_query = """
        SELECT
            insight_id,
            insight,
            model_name,
            generated_at
        FROM ai_insights
        ORDER BY generated_at DESC
        LIMIT 1
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:

            cursor.execute(summary_query)
            summary_row = cursor.fetchone()

            cursor.execute(results_query)
            result_rows = cursor.fetchall()

            cursor.execute(rules_query)
            rules_row = cursor.fetchone()

            cursor.execute(insight_query)
            insight_row = cursor.fetchone()

    return {
        "summary": {
            "total_failures": summary_row[0],
            "failed_events": summary_row[1],
            "failing_rules": summary_row[2],
        },
        "rules": {
            "active": rules_row[0],
            "disabled": rules_row[1],
        },
        "recent_failures": [
            {
                "result_id": row[0],
                "event_id": row[1],
                "rule_type": row[2],
                "column_name": row[3],
                "failure_message": row[4],
                "processed_at": row[5],
            }
            for row in result_rows
        ],
        "latest_ai_insight": (
            {
                "insight_id": insight_row[0],
                "insight": insight_row[1],
                "model_name": insight_row[2],
                "generated_at": insight_row[3],
            }
            if insight_row
            else None
        ),
    }

@router.get("/rules")
def get_rules():
    query = """
        SELECT
            rule_id,
            dataset_name,
            rule_type,
            column_name,
            rule_config,
            enabled,
            created_at
        FROM dq_rules
        ORDER BY rule_id
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return [
        {
            "rule_id": row[0],
            "dataset_name": row[1],
            "rule_type": row[2],
            "column_name": row[3],
            "rule_config": row[4],
            "enabled": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]


@router.get("/results")
def get_results(limit: int = 100):
    query = """
        SELECT
            result_id,
            event_id,
            dataset_name,
            rule_id,
            rule_type,
            column_name,
            failure_message,
            source_topic,
            source_partition,
            source_offset,
            processed_at
        FROM dq_results
        ORDER BY processed_at DESC
        LIMIT %s
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()

    return [
        {
            "result_id": row[0],
            "event_id": row[1],
            "dataset_name": row[2],
            "rule_id": row[3],
            "rule_type": row[4],
            "column_name": row[5],
            "failure_message": row[6],
            "source_topic": row[7],
            "source_partition": row[8],
            "source_offset": row[9],
            "processed_at": row[10],
        }
        for row in rows
    ]


@router.get("/summary")
def get_summary():
    query = """
        SELECT
            COUNT(*) AS total_failures,
            COUNT(DISTINCT event_id) AS failed_events,
            COUNT(DISTINCT rule_id) AS failing_rules
        FROM dq_results
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    return {
        "total_failures": row[0],
        "failed_events": row[1],
        "failing_rules": row[2],
    }


@router.get("/insights")
def get_insights():
    query = """
        SELECT
            rule_type,
            column_name,
            COUNT(*) AS failure_count
        FROM dq_results
        GROUP BY
            rule_type,
            column_name
        ORDER BY failure_count DESC
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:

            cursor.execute(query)
            rows = cursor.fetchall()

    total_failures = sum(row[2] for row in rows)

    failed_events_query = """
        SELECT COUNT(DISTINCT event_id)
        FROM dq_results
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:

            cursor.execute(failed_events_query)
            failed_events = cursor.fetchone()[0]

    rule_failures = [
        {
            "rule_type": row[0],
            "column_name": row[1],
            "failure_count": row[2],
        }
        for row in rows
    ]

    dq_summary = {
        "dataset": "transactions",
        "total_failures": total_failures,
        "failed_events": failed_events,
        "rule_failures": rule_failures,
    }

    prompt = f"""
Analyze the following data quality results.

DATA QUALITY SUMMARY:

{json.dumps(dq_summary, indent=2)}

Return ONLY valid JSON using exactly this structure:

{{
    "severity": "LOW | MEDIUM | HIGH | CRITICAL",
    "summary": "Short summary of the overall situation.",
    "top_issues": [
        {{
            "rule": "Rule type",
            "column": "Column name",
            "failure_count": 0
        }}
    ],
    "possible_causes": [
        "Possible cause supported by the available evidence."
    ],
    "impact": [
        "Potential impact based only on the supplied data."
    ],
    "recommended_actions": [
        "Practical recommended action."
    ]
}}

Important:
- Only use evidence present in the supplied data.
- Clearly treat causes as hypotheses.
- Do not invent upstream systems or business processes.
- Keep the response concise.
"""

    insight_text = generate_insight(prompt)

    insight = json.loads(insight_text)

    save_insight(
    dataset_name=dq_summary["dataset"],
    total_failures=dq_summary["total_failures"],
    failed_events=dq_summary["failed_events"],
    insight=insight,
    model_name="qwen3:4b",
    )

    return {
        "summary": dq_summary,
        "ai_insight": insight,
    }

@router.get("/insights/latest")
def get_latest_insight():
    query = """
        SELECT
            insight_id,
            dataset_name,
            total_failures,
            failed_events,
            insight,
            model_name,
            generated_at
        FROM ai_insights
        ORDER BY generated_at DESC
        LIMIT 1
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    if row is None:
        return {
            "message": "No AI insights available"
        }

    return {
        "insight_id": row[0],
        "dataset_name": row[1],
        "total_failures": row[2],
        "failed_events": row[3],
        "ai_insight": row[4],
        "model_name": row[5],
        "generated_at": row[6],
    }


@router.get("/insights/history")
def get_insight_history(limit: int = 20):
    query = """
        SELECT
            insight_id,
            dataset_name,
            total_failures,
            failed_events,
            insight,
            model_name,
            generated_at
        FROM ai_insights
        ORDER BY generated_at DESC
        LIMIT %s
    """

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()

    return [
        {
            "insight_id": row[0],
            "dataset_name": row[1],
            "total_failures": row[2],
            "failed_events": row[3],
            "ai_insight": row[4],
            "model_name": row[5],
            "generated_at": row[6],
        }
        for row in rows
    ]