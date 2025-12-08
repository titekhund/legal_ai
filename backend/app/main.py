"""
FastAPI application entry point for Legal AI system
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import chat, conversations, health
from app.core import (
    get_logger,
    get_settings,
    register_exception_handlers,
    set_request_id,
    setup_logging,
)
from app.services import TaxCodeService

# Initialize logger
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_window} seconds"]
)

# Global service instances
tax_service: TaxCodeService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Legal AI application...")

    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        environment=settings.environment
    )

    # Initialize tax service
    global tax_service
    tax_service = TaxCodeService()

    try:
        logger.info("Initializing Tax Code Service...")
        await tax_service.initialize()
        logger.info("Tax Code Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Tax Code Service: {e}")
        logger.warning("Tax Code Service will not be available")

    # Set tax service in route handlers
    health.set_tax_service(tax_service)
    chat.set_tax_service(tax_service)

    logger.info(f"Legal AI application started in {settings.environment} mode")

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down Legal AI application...")


# Create FastAPI application
app = FastAPI(
    title="Legal AI API",
    description="AI-powered legal assistant for Georgian Tax Code and legal research",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# Middleware
# ============================================================================


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID Middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    import uuid

    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)"
    )

    return response


# ============================================================================
# Register Exception Handlers
# ============================================================================


register_exception_handlers(app)


# ============================================================================
# API Routes
# ============================================================================


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Legal AI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# Include API v1 routers
app.include_router(
    health.router,
    prefix="/v1",
    tags=["health"]
)

app.include_router(
    chat.router,
    prefix="/v1",
    tags=["chat"]
)

app.include_router(
    conversations.router,
    prefix="/v1",
    tags=["conversations"]
)


# ============================================================================
# Run Application
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development(),
        log_level=settings.log_level.lower()
    )
