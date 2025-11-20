"""Character Sheet Generator - FastAPI Application.

This is the main application entry point that initializes the FastAPI server,
configures middleware, registers routes, and sets up error handling.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import register_exception_handlers
from app.api.routes import character
from app.config import settings
from app.core.logger import get_logger, setup_logging
from app.database import InsertCharacterSheetinDatabase

# Initialize logging
setup_logging(log_level=settings.log_level)
logger = get_logger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    logger.info("Initializing Character Sheet Generator application")

    # Create FastAPI app
    app = FastAPI(
        title="Character Sheet Generator API",
        version="1.0.0",
        description=(
            "AI-powered NPC character sheet generator for the Aetheria world. "
            "Generate complete, detailed character sheets from simple seed descriptions "
            "using Google's Gemini LLM via Vertex AI."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Configure CORS (adjust origins as needed for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Register routers
    app.include_router(
        character.router,
        prefix="/api/v1",
        tags=["Character Generation"]
    )

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Run on application startup."""
        logger.info("=" * 60)
        logger.info("Character Sheet Generator API Starting")
        logger.info("=" * 60)
        logger.info(f"Environment: {'DEBUG' if settings.debug else 'PRODUCTION'}")
        logger.info(f"Google Cloud Project: {settings.google_cloud_project}")
        logger.info(f"Gemini Model: {settings.gemini_model}")
        logger.info(f"Templates Directory: {settings.templates_dir}")
        logger.info(f"Output Directory: {settings.output_dir}")
        logger.info("=" * 60)

        # Validate templates on startup
        try:
            from app.services.template_manager import TemplateManager
            template_manager = TemplateManager(settings.templates_dir)
            template_manager.validate_templates()
            logger.info("✓ Templates validated successfully")
        except Exception as e:
            logger.error(f"✗ Template validation failed: {str(e)}")
            logger.warning("Application started but template issues detected")

    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Run on application shutdown."""
        logger.info("Character Sheet Generator API Shutting Down")

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Character Sheet Generator API",
            "version": "1.0.0",
            "status": "running",
            "documentation": "/docs",
            "health_check": "/api/v1/health"
        }

    logger.info("FastAPI application configured successfully")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

    
