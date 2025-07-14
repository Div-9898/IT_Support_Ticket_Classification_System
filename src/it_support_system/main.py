from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
from typing import List

from .config.settings import settings
from .utils.logging import setup_logging, get_logger, log_request
from .utils.exceptions import ITSupportException
from .models.database import create_tables
from .api.auth import router as auth_router
from .api.tickets import router as tickets_router
from .api.users import router as users_router
from .api.dashboard import router as dashboard_router
from .api.search import router as search_router
from .api.upload import router as upload_router
from .services.ml_service import MLService

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize ML service (will be initialized in lifespan)
ml_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting IT Support Ticket Classification System")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Initialize ML service
    global ml_service
    try:
        ml_service = MLService()
        await ml_service.initialize()
        logger.info("ML service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ML service: {e}")
        # Don't raise here - allow app to start without ML service
        ml_service = None
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IT Support Ticket Classification System")
    if ml_service:
        await ml_service.cleanup()
    logger.info("Application shutdown completed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered IT Support Ticket Classification and Management System",
    version=settings.app_version,
    docs_url=settings.docs_url if settings.enable_docs else None,
    redoc_url=settings.redoc_url if settings.enable_docs else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else [settings.host]
)

# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all HTTP requests."""
    return await log_request(request, call_next)

# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Monitor request performance."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(ITSupportException)
async def it_support_exception_handler(request: Request, exc: ITSupportException):
    """Handle custom IT Support exceptions."""
    logger.error(f"IT Support Exception: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": exc.message,
            "error_code": exc.__class__.__name__,
            "details": exc.details,
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "errors": exc.errors(),
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": "HTTP_ERROR",
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "ml_service_ready": ml_service.is_ready() if ml_service else False,
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "IT Support Ticket Classification System API",
        "version": settings.app_version,
        "docs_url": f"{settings.docs_url}" if settings.enable_docs else None,
    }

# Include routers
app.include_router(
    auth_router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["Authentication"]
)

app.include_router(
    tickets_router,
    prefix=f"{settings.api_prefix}/tickets",
    tags=["Tickets"]
)

app.include_router(
    users_router,
    prefix=f"{settings.api_prefix}/users",
    tags=["Users"]
)

app.include_router(
    dashboard_router,
    prefix=f"{settings.api_prefix}/dashboard",
    tags=["Dashboard"]
)

app.include_router(
    search_router,
    prefix=f"{settings.api_prefix}/search",
    tags=["Search"]
)

app.include_router(
    upload_router,
    prefix=f"{settings.api_prefix}/upload",
    tags=["Upload"]
)

# Startup message
logger.info(f"FastAPI application configured with prefix: {settings.api_prefix}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_level=settings.log_level.lower(),
    )