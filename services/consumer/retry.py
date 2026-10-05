MAX_RETRIES = 3


def get_retry_count(event: dict) -> int:
    return int(event.get("_retry_count", 0))


def increment_retry_count(event: dict) -> dict:
    event["_retry_count"] = get_retry_count(event) + 1
    return event


def should_retry(event: dict) -> bool:
    return get_retry_count(event) < MAX_RETRIES