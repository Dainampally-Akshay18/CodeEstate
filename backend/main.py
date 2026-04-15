"""
Tech Monopoly Backend - Entry Point
Real-time multiplayer Monopoly-style board game
"""

import uvicorn
from app.main import app


if __name__ == "__main__":
    """
    Run FastAPI application with Uvicorn server.
    """
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload on file changes
    )
