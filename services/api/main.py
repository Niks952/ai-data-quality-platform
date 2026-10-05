from fastapi import FastAPI

from services.api.routes.dq import router as dq_router


app = FastAPI(
    title="AI Data Quality Platform",
    description="Real-time data quality platform powered by Kafka and PostgreSQL",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


app.include_router(dq_router)