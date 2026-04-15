"""
Models module for data structures.
Contains Pydantic models for request/response handling.
"""

from pydantic import BaseModel


class BaseResponseModel(BaseModel):
    """Base response model for all API responses."""

    success: bool
    message: str


class ErrorResponseModel(BaseResponseModel):
    """Error response model."""

    error: str
