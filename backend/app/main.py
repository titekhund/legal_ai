"""
FastAPI application entry point for Legal AI system
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import admin, auth, chat, conversations, documents, health
from app.core import (
    get_logger,
    get_settings,
    register_exception_handlers,
    set_request_id,
    setup_logging,
)
from app.services import DisputeService, DocumentService, Orchestrator, TaxCodeService

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
dispute_service: DisputeService = None
document_service: DocumentService = None
orchestrator: Orchestrator = None


async def initialize_services_background():
    """
    Initialize services in background (non-blocking for Cloud Run startup)
    """
    global tax_service, dispute_service, document_service, orchestrator

    # Initialize tax service
    tax_service = TaxCodeService()

    try:
        logger.info("Initializing Tax Code Service...")
        await tax_service.initialize()
        logger.info("Tax Code Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Tax Code Service: {e}")
        logger.warning("Tax Code Service will not be available")

    # Initialize dispute service
    dispute_service = DisputeService()

    try:
        logger.info("Initializing Dispute Service...")
        await dispute_service.initialize()
        logger.info("Dispute Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Dispute Service: {e}")
        logger.warning("Dispute Service will not be available")

    # Initialize document service
    document_service = DocumentService()

    try:
        logger.info("Initializing Document Service...")
        await document_service.initialize()
        logger.info("Document Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Document Service: {e}")
        logger.warning("Document Service will not be available")

    # Initialize orchestrator
    orchestrator = Orchestrator(
        tax_service=tax_service,
        dispute_service=dispute_service
    )
    logger.info("Orchestrator initialized")

    # Set services in route handlers
    health.set_tax_service(tax_service)
    chat.set_tax_service(tax_service)
    chat.set_orchestrator(orchestrator)
    documents.set_document_service(document_service)
    admin.set_services(tax_service, dispute_service, document_service)

    logger.info("All services initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events

    Note: Service initialization runs in background to allow fast startup
    for Cloud Run health checks. The /health endpoint returns immediately,
    while /status shows actual service readiness.
    """
    import asyncio
    from app.db import init_db, close_db

    # Startup
    logger.info("Starting Legal AI application...")

    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        environment=settings.environment
    )

    # Initialize database
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Database features will not be available")

    # Start service initialization in background (non-blocking)
    # This allows the server to start quickly and respond to health checks
    logger.info("Starting background service initialization...")
    asyncio.create_task(initialize_services_background())

    logger.info(f"Legal AI application started in {settings.environment} mode")
    logger.info("Server ready to accept requests (services initializing in background)")

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down Legal AI application...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Georgian Legal AI API",
    description=(
        "AI-powered legal assistant for Georgian Tax Code and legal research | "
        "ხელოვნური ინტელექტის იურიდიული ასისტენტი საქართველოს საგადასახადო კოდექსისა და სამართლებრივი კვლევებისთვის"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and service status endpoints | სერვისის სტატუსის შემოწმება"
        },
        {
            "name": "auth",
            "description": "User authentication and registration | მომხმარებლის ავტორიზაცია და რეგისტრაცია"
        },
        {
            "name": "chat",
            "description": "Chat with AI legal assistant | ჩატი AI იურიდიულ ასისტენტთან"
        },
        {
            "name": "conversations",
            "description": "Manage conversation history | საუბრების ისტორიის მართვა"
        },
        {
            "name": "documents",
            "description": "Generate legal documents from templates | იურიდიული დოკუმენტების გენერირება შაბლონებიდან"
        },
        {
            "name": "admin",
            "description": "Admin endpoints for content management | ადმინისტრატორის ინტერფეისი"
        }
    ],
    responses={
        400: {
            "description": "Bad Request - Invalid input parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid request parameters",
                            "details": {"field": "message", "issue": "Field required"}
                        },
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests",
                            "details": {"retry_after": 60}
                        },
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected error occurred",
                            "details": {}
                        },
                        "request_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        }
    }
)

# Add rate limiter to app state
app.state.limiter = limiter


# ============================================================================
# Middleware
# ============================================================================
#
# Middleware execution order (incoming request):
# 1. CORS Middleware (outermost layer)
# 2. Request ID Middleware
# 3. Logging Middleware
# 4. Route Handler (with rate limiting)
# 5. Exception Handlers
#
# Note: Middleware added with add_middleware() runs before @app.middleware()
# ============================================================================


# CORS Middleware - Runs first (outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID Middleware - Runs second
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Add unique request ID to each request
    This ID is used for logging and error tracking
    """
    import uuid

    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Logging Middleware - Runs third
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all requests with timing
    Uses request_id set by previous middleware
    """
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


# Custom exception handler to ensure all errors include request_id
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that ensures all errors include request_id"""
    from app.core.logging import request_id_var

    request_id = request_id_var.get()

    # Log the exception
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )

    # Return structured error response
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"exception": type(exc).__name__}
            },
            "request_id": request_id
        }
    )


# Custom rate limit exception handler with request_id
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Rate limit exception handler with structured response"""
    from app.core.logging import request_id_var

    request_id = request_id_var.get()

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {"retry_after": 60}
            },
            "request_id": request_id
        },
        headers={"Retry-After": "60"}
    )


register_exception_handlers(app)


# ============================================================================
# API Routes
# ============================================================================


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint | მთავარი გვერდი

    Returns basic API information and documentation links
    """
    return {
        "name": "Georgian Legal AI API",
        "name_ka": "ქართული იურიდიული AI API",
        "version": "1.0.0",
        "status": "running",
        "description": "AI-powered legal assistant for Georgian Tax Code and legal research",
        "description_ka": "ხელოვნური ინტელექტის იურიდიული ასისტენტი საქართველოს საგადასახადო კოდექსისა და სამართლებრივი კვლევებისთვის",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Root-level health check for Cloud Run
@app.get("/health")
async def root_health():
    """
    Root-level health check for Cloud Run and load balancers

    This endpoint returns immediately without checking service status.
    Use /v1/status for detailed service readiness.
    """
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# Include API v1 routers
app.include_router(
    health.router,
    prefix="/v1",
    tags=["health"]
)

app.include_router(
    auth.router,
    prefix="/v1",
    tags=["auth"]
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

app.include_router(
    documents.router,
    prefix="/v1",
    tags=["documents"]
)

app.include_router(
    admin.router,
    prefix="/v1",
    tags=["admin"]
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
