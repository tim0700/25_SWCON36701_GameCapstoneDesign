"""
Main Application Module - FastAPI server for NPC Dynamic Memory System.

This module coordinates:
- Configuration loading from .env
- Database and service initialization
- API router registration
- Middleware and exception handling
- Startup and shutdown event management
"""
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import chromadb

from config import settings
from services.recent_memory import RecentMemoryService
from services.longterm_memory import LongTermMemoryService
from services.memory_manager import MemoryManager
from utils.embeddings import EmbeddingService
from api import memory as memory_router_module
from api import admin as admin_router_module
from api import quest as quest_router_module  # NEW: Quest generation

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging() -> None:
    """Configure Python logging with settings from configuration."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title=settings.api_title,
    description="REST API for NPC memory management with vector embeddings",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:*",
        "http://127.0.0.1",
        "http://127.0.0.1:*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
)

# ============================================================================
# GLOBAL SERVICE INSTANCES (initialized in startup event)
# ============================================================================

chroma_client = None
embedding_service = None
recent_memory_service = None
longterm_memory_service = None
memory_manager = None

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "detail": exc.errors()
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError as bad request."""
    logger.warning(f"ValueError on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "message": str(exc),
            "error_code": "VALIDATION_ERROR"
        }
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    """Handle RuntimeError as internal server error."""
    logger.error(f"RuntimeError on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.error(
        f"Unhandled exception on {request.url.path}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "detail": str(exc) if settings.log_level == "DEBUG" else "An error occurred"
        }
    )


# ============================================================================
# STARTUP EVENT HANDLER
# ============================================================================

@app.on_event("startup")
async def startup_event() -> None:
    """
    Initialize all services and dependencies on application startup.

    Sequence:
    1. Create data directories
    2. Initialize ChromaDB client
    3. Initialize embedding service
    4. Preload embedding model (if configured)
    5. Initialize recent memory service and restore from backup
    6. Initialize long-term memory service
    7. Initialize memory manager
    8. Inject dependencies into API routers
    """
    global chroma_client, embedding_service, recent_memory_service
    global longterm_memory_service, memory_manager

    logger.info("=" * 70)
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info("=" * 70)

    try:
        # 1. Create data directories
        logger.info("Creating data directories...")
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.buffer_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.recent_memory_backup).parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"  - ChromaDB directory: {settings.chroma_persist_dir}")
        logger.debug(f"  - Buffer directory: {settings.buffer_dir}")
        logger.debug(f"  - Recent memory backup: {settings.recent_memory_backup}")

        # 2. Initialize ChromaDB client
        logger.info("Initializing ChromaDB client...")
        chroma_client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir)
        )
        logger.info(f"  ChromaDB initialized at {settings.chroma_persist_dir}")

        # 3. Initialize embedding service
        logger.info("Initializing Embedding Service...")
        embedding_service = EmbeddingService(
            model_name=settings.embedding_model,
            device=settings.embedding_device
        )
        logger.info(f"  Embedding service created (model: {settings.embedding_model})")

        # 4. Preload embedding model (if configured)
        if settings.preload_on_startup:
            logger.info("Preloading embedding model (this may take a few seconds)...")
            embedding_service.warmup()
            logger.info("  Embedding model preloaded successfully")
        else:
            logger.info("  Model will load on first use (preload disabled)")

        # 5. Initialize recent memory service
        logger.info("Initializing Recent Memory Service...")
        recent_memory_service = RecentMemoryService(
            max_size=settings.recent_memory_size
        )
        logger.info(f"  Recent memory service initialized (max_size={settings.recent_memory_size})")

        # Restore from backup if exists
        backup_path = Path(settings.recent_memory_backup)
        if backup_path.exists():
            logger.info(f"Restoring recent memories from backup: {backup_path}")
            recent_memory_service.load_from_disk(str(backup_path))
            logger.info("  Recent memories restored successfully")
        else:
            logger.debug("  No backup file found - starting with empty recent memory")

        # 6. Initialize long-term memory service
        logger.info("Initializing Long-term Memory Service...")
        longterm_memory_service = LongTermMemoryService(
            chroma_client=chroma_client,
            embedding_service=embedding_service,
            buffer_dir=settings.buffer_dir,
            buffer_size=settings.long_term_buffer_size
        )
        logger.info(f"  Long-term memory service initialized (buffer_size={settings.long_term_buffer_size})")

        # 7. Initialize memory manager
        logger.info("Initializing Memory Manager...")
        memory_manager = MemoryManager(
            recent_service=recent_memory_service,
            longterm_service=longterm_memory_service
        )
        logger.info("  Memory manager initialized successfully")

        # 8. Inject dependencies into API routers
        logger.info("Injecting dependencies into API routers...")
        memory_router_module.set_memory_manager(memory_manager)
        admin_router_module.set_memory_manager(memory_manager)
        admin_router_module.set_embedding_service(embedding_service)
        admin_router_module.set_chroma_client(chroma_client)
        quest_router_module.set_memory_manager(memory_manager)  # NEW: Quest generation
        logger.info("  Dependencies injected successfully")

        # Startup complete
        logger.info("=" * 70)
        logger.info(f"Server ready on http://{settings.api_host}:{settings.api_port}")
        logger.info(f"  - API Documentation: http://{settings.api_host}:{settings.api_port}/docs")
        logger.info(f"  - ReDoc: http://{settings.api_host}:{settings.api_port}/redoc")
        logger.info(f"  - Health Check: http://{settings.api_host}:{settings.api_port}/admin/health")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise


# ============================================================================
# SHUTDOWN EVENT HANDLER
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Save state and cleanup on application shutdown.

    Tasks:
    1. Save recent memories to disk
    2. Log shutdown completion
    """
    logger.warning("=" * 70)
    logger.warning("Shutting down server...")
    logger.warning("=" * 70)

    try:
        # Save recent memories to backup
        if recent_memory_service is not None:
            logger.info(f"Saving recent memories to {settings.recent_memory_backup}...")
            recent_memory_service.save_to_disk(str(settings.recent_memory_backup))
            logger.info("  Recent memories saved successfully")
        else:
            logger.warning("  Recent memory service not initialized - nothing to save")

        logger.warning("=" * 70)
        logger.warning("Server stopped")
        logger.warning("=" * 70)

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

# Register API routers
app.include_router(
    memory_router_module.router,
    tags=["Memory Operations"]
)

app.include_router(
    admin_router_module.router,
    tags=["Admin Operations"]
)

app.include_router(
    quest_router_module.router,  # NEW: Quest generation
    tags=["Quest Generation"]
)

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    API root endpoint - redirects to documentation.

    Returns basic API information and links to documentation.
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "memory": "/memory",
            "admin": "/admin",
            "health": "/admin/health"
        }
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Run the application using uvicorn.

    For development: python main.py
    For production: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    """
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
