"""
Centralized Error Handling & Response Utilities.

Provides standardized error responses and exception conversion
for consistent error handling across all routes.

Phase 10: Production-Ready Error Handling
"""

from fastapi import HTTPException, status
from typing import Dict, Any, Optional, Type
from functools import wraps
from app.services.property_service import (
    PropertyServiceError,
    InvalidPropertyError,
    PropertyOwnedError,
    InsufficientFundsError,
    InvalidTurnError,
    GameOverError,
    PlayerBankruptError,
    StaleStateError,
)
from app.db.firebase import FirebaseOperationError


# ============================================================================
# ERROR RESPONSE MAPPING
# ============================================================================

EXCEPTION_TO_STATUS = {
    InvalidTurnError: status.HTTP_400_BAD_REQUEST,
    PlayerBankruptError: status.HTTP_400_BAD_REQUEST,
    GameOverError: status.HTTP_400_BAD_REQUEST,
    PropertyOwnedError: status.HTTP_409_CONFLICT,
    InsufficientFundsError: status.HTTP_400_BAD_REQUEST,
    InvalidPropertyError: status.HTTP_404_NOT_FOUND,
    StaleStateError: status.HTTP_409_CONFLICT,
    FirebaseOperationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    PropertyServiceError: status.HTTP_400_BAD_REQUEST,
}


# ============================================================================
# ERROR CONVERSION UTILITIES
# ============================================================================

def service_exception_to_http(
    exc: Exception,
    default_status: int = status.HTTP_400_BAD_REQUEST
) -> HTTPException:
    """
    Convert service exception to HTTP exception.
    
    Maps known exceptions to appropriate HTTP status codes with
    meaningful error messages.
    
    Args:
        exc: Exception from service layer.
        default_status: Status code if exception type not recognized.
        
    Returns:
        HTTPException: HTTP-friendly exception
    """
    exc_type = type(exc)
    http_status = EXCEPTION_TO_STATUS.get(exc_type, default_status)
    
    return HTTPException(
        status_code=http_status,
        detail=str(exc)
    )


def handle_service_exceptions(func):
    """
    Decorator to handle service layer exceptions and convert to HTTP exceptions.
    
    Catches known service exceptions and converts them to appropriate HTTP responses.
    Unexpected exceptions are logged and returned as 500 Internal Server Error.
    
    Usage:
        @router.post("/endpoint")
        @handle_service_exceptions
        async def my_endpoint(request: Request):
            ...
            
    Args:
        func: Async endpoint function to wrap.
        
    Returns:
        Wrapped function with exception handling.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (
            InvalidTurnError,
            PlayerBankruptError,
            GameOverError,
            PropertyOwnedError,
            InsufficientFundsError,
            InvalidPropertyError,
            StaleStateError,
            PropertyServiceError,
            FirebaseOperationError,
        ) as e:
            raise service_exception_to_http(e)
        except HTTPException:
            # Already an HTTPException, re-raise as-is
            raise
        except Exception as e:
            # Unexpected error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
    
    return wrapper


# ============================================================================
# STANDARD ERROR RESPONSE BUILDERS
# ============================================================================

def error_response(
    error: str,
    details: Optional[str] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> HTTPException:
    """
    Create a standardized error response.
    
    Args:
        error: Main error message.
        details: Optional detailed explanation.
        status_code: HTTP status code.
        
    Returns:
        HTTPException: Formatted error response.
    """
    detail_msg = error
    if details:
        detail_msg = f"{error} - {details}"
    
    return HTTPException(
        status_code=status_code,
        detail=detail_msg
    )


def validation_error(message: str) -> HTTPException:
    """
    Create validation error response (400 Bad Request).
    
    Args:
        message: Validation error message.
        
    Returns:
        HTTPException: 400 validation error.
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )


def not_found_error(resource: str, resource_id: str) -> HTTPException:
    """
    Create not found error response (404).
    
    Args:
        resource: Type of resource (e.g., "Room", "Player", "Property").
        resource_id: ID of missing resource.
        
    Returns:
        HTTPException: 404 not found error.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} '{resource_id}' not found"
    )


def conflict_error(message: str) -> HTTPException:
    """
    Create conflict error response (409).
    
    Args:
        message: Conflict error message.
        
    Returns:
        HTTPException: 409 conflict error.
    """
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message
    )


def internal_error(message: str) -> HTTPException:
    """
    Create internal error response (500).
    
    Args:
        message: Error message.
        
    Returns:
        HTTPException: 500 internal server error.
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )
