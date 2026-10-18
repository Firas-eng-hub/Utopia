"""
UtopiaHire API - Main Application
FastAPI application entry point with all routers and middleware
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
logger_init = logging.getLogger(__name__)
logger_init.info(f"✅ Loaded environment from: {env_path}")
logger_init.info(f"   GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")

from app.core.config import settings
from app.core.database import db_manager

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting UtopiaHire API...")
    logger.info("Database configuration loaded")
    logger.info(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    
    # Test database connection
    try:
        db = db_manager.get_db()
        result = db.execute_query("SELECT COUNT(*) as count FROM users")
        logger.info(f"Database connected successfully. Users in database: {result[0]['count']}")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down UtopiaHire API...")
    db_manager.close()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    # Convert bytes to strings in error details and make everything JSON serializable
    errors = []
    for error in exc.errors():
        serializable_error = {}
        for key, value in error.items():
            if isinstance(value, bytes):
                serializable_error[key] = value.decode('utf-8', errors='replace')
            elif isinstance(value, dict):
                # Handle nested dicts (like 'ctx')
                serializable_dict = {}
                for k, v in value.items():
                    if isinstance(v, bytes):
                        serializable_dict[k] = v.decode('utf-8', errors='replace')
                    else:
                        # Convert any other non-serializable objects to strings
                        try:
                            import json
                            json.dumps(v)
                            serializable_dict[k] = v
                        except (TypeError, ValueError):
                            serializable_dict[k] = str(v)
                serializable_error[key] = serializable_dict
            else:
                # Convert any other non-serializable objects to strings
                try:
                    import json
                    json.dumps(value)
                    serializable_error[key] = value
                except (TypeError, ValueError):
                    serializable_error[key] = str(value)
        errors.append(serializable_error)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": errors
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.DEBUG else None
            }
        }
    )


# Health check endpoints
@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Fail deployment readiness when the database cannot serve requests."""
    try:
        db_manager.get_db().execute_query("SELECT COUNT(*) FROM users")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME
    }


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
async def health_check_v1():
    """
    Detailed health check with service status
    
    Returns:
        dict: Health status of API and all services
    """
    db_status = "connected"
    try:
        db = db_manager.get_db()
        db.execute_query("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.VERSION,
        "timestamp": time.time(),
        "database": db_status,
        "services": {
            "resume_parser": True,
            "job_scraper": True,
            "interview_analyzer": True,
            "footprint_scanner": True
        }
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    if serve_frontend:
        return FileResponse(frontend_dist / "index.html")
    return {
        "message": "Welcome to UtopiaHire API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


# Import and include routers
from app.api import auth, resume, jobs, interview

app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(resume.router, prefix=f"{settings.API_V1_PREFIX}/resumes", tags=["Resume"])
app.include_router(jobs.router, tags=["Jobs"])  # Jobs router has its own prefix
app.include_router(interview.router, tags=["Interview Simulator"])  # Interview router has its own prefix

# Footprint Scanner Module
try:
    from app.api import footprint
    app.include_router(footprint.router, tags=["Footprint"])  # Footprint router has its own prefix
    logger.info("✅ Footprint Scanner module loaded")
except Exception as e:
    logger.warning(f"⚠️  Footprint Scanner module not loaded: {e}")


# The production container can serve the React app and API from one origin.
# API routes are registered first; unknown API paths must retain a JSON 404.
serve_frontend = os.getenv("SERVE_FRONTEND", "false").lower() == "true"
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if serve_frontend:
    if not (frontend_dist / "index.html").is_file():
        raise RuntimeError("SERVE_FRONTEND requires a built frontend/dist directory")
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{frontend_path:path}", include_in_schema=False)
    async def frontend_page(frontend_path: str):
        if frontend_path == "api" or frontend_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (frontend_dist / frontend_path).resolve()
        if not candidate.is_relative_to(frontend_dist.resolve()):
            raise HTTPException(status_code=404, detail="Not found")
        if candidate.is_file():
            return FileResponse(candidate)
        if Path(frontend_path).suffix:
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(frontend_dist / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
