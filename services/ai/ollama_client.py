import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"


def generate_insight(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior data quality and data engineering "
                    "analyst. Analyze data quality failures using only "
                    "the evidence provided."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "format": "json",
        "options": {
            "temperature": 0,
            "num_predict": 300,
        },
        "stream": False,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]