"""
Health check endpoint.
Used for monitoring app status and readiness.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    message: str


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Current application health status
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        message="Tech Monopoly Backend is running",
    )
