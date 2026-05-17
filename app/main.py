from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    description="A centralized Data Loss Prevention API Gateway for LLM sanitization."
)

logger.info("Initializing PII Proxy Gateway Application")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "0.1.0"
    }

# Include API Router
app.include_router(api_router)
