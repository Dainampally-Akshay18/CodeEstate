"""
FastAPI application factory and setup.
Creates and configures the FastAPI app instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes import health

settings = get_settings()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="Real-time multiplayer Monopoly-style board game",
        version=settings.app_version,
        debug=settings.debug,
    )

    # Configure CORS for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Phase 5: Configure specific origins from .env
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register health check routes
    app.include_router(health.router)

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "ready",
        }

    return app


# Create app instance
app = create_app()
