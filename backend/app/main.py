import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import RequestIDMiddleware, setup_logging
from app.db.session import async_session_factory
from app.schemas.health import HealthResponse
from app.services.auth import seed_demo_user
from app.services.health import get_system_health
from app.api.v1.router import api_v1_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured JSON logging
    setup_logging(settings.LOG_LEVEL)

    # Idempotently seed demo user on startup
    try:
        async with async_session_factory() as session:
            await seed_demo_user(session)
    except Exception as e:
        logger.warning(f"Could not seed demo user on startup (DB may still be initializing): {str(e)}")

    yield
    # Shutdown cleanups if needed


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="TradeWise - AI-Assisted Paper Trading & Portfolio Intelligence Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Register Custom Request ID Middleware
app.add_middleware(RequestIDMiddleware)

# Register CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register Global Error Handlers (Standard Error Envelope)
register_error_handlers(app)

# Root Health Check
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root health check",
    description="Returns backend process, database, and Redis health status.",
)
async def root_health_check() -> HealthResponse:
    return await get_system_health()


# Mount API v1 Router
app.include_router(api_v1_router)
