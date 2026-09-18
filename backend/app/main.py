"""InvoiceIQ API — application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import analysis as analysis_api
from .api import dashboard as dashboard_api
from .api import demo as demo_api
from .api import documents as documents_api
from .api import export as export_api
from .api import invoices as invoices_api
from .api import review as review_api
from .config import get_settings
from .database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables on startup (no migration tooling needed for the MVP)
    init_db()
    yield


app = FastAPI(
    title="InvoiceIQ API",
    description="AI-powered invoice verification & risk intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(invoices_api.router)
app.include_router(analysis_api.router)
app.include_router(review_api.router)
app.include_router(dashboard_api.router)
app.include_router(demo_api.router)
app.include_router(documents_api.router)
app.include_router(export_api.router)


@app.get("/api/health")
def health() -> dict:
    """Lightweight health/liveness check used by the frontend."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "ai_configured": bool(settings.openai_api_key),
    }
