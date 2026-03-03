import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from api.config import settings
from api.routers import health, verification
from core.exceptions import (
    RateLimitExceededError,
    SessionNotFoundError,
    ValidationError,
    VerifIDError,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    # Startup
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if settings.is_development else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(settings.app_log_level)
        ),
    )
    logger.info("verifid.startup", env=settings.app_env)
    yield
    # Shutdown
    logger.info("verifid.shutdown")


app = FastAPI(
    title="VerifID — Identity Verification API",
    version="0.1.0",
    description="KYC identity verification system",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# --- Middleware ---

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: object) -> Response:
    """Attach a unique request ID to every request."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response: Response = await call_next(request)  # type: ignore[misc]
    response.headers["X-Request-ID"] = request_id
    return response


# --- Exception Handlers ---


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(request: Request, exc: SessionNotFoundError) -> ORJSONResponse:
    return ORJSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=429,
        content={"detail": exc.message},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError) -> ORJSONResponse:
    return ORJSONResponse(status_code=422, content={"detail": exc.message, "errors": exc.details})


@app.exception_handler(VerifIDError)
async def verifid_error_handler(request: Request, exc: VerifIDError) -> ORJSONResponse:
    return ORJSONResponse(status_code=500, content={"detail": exc.message})


# --- Routers ---

app.include_router(health.router)
app.include_router(verification.router)
