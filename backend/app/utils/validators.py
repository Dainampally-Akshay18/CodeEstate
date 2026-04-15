"""
Validation Utilities - Centralized input validation.

Provides reusable validation functions for common request parameters
to reduce duplication and ensure consistency across all endpoints.

Phase 10: Centralized Validation
"""

from typing import Optional
from fastapi import HTTPException, status


# ============================================================================
# STRING VALIDATION
# ============================================================================

def validate_string(value: Optional[str], field_name: str, allow_empty: bool = False) -> str:
    """
    Validate a string parameter.
    
    Args:
        value: String value to validate.
        field_name: Name of field (for error messages).
        allow_empty: Whether to allow empty strings. Default: False.
        
    Returns:
        Stripped string value.
        
    Raises:
        HTTPException: If validation fails.
    """
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required"
        )
    
    stripped = value.strip() if isinstance(value, str) else str(value)
    
    if not allow_empty and not stripped:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty"
        )
    
    return stripped


def validate_room_id(room_id: Optional[str]) -> str:
    """
    Validate room ID parameter.
    
    Args:
        room_id: Room ID to validate.
        
    Returns:
        Validated room ID.
        
    Raises:
        HTTPException: If validation fails.
    """
    return validate_string(room_id, "room_id", allow_empty=False)


def validate_player_id(player_id: Optional[str]) -> str:
    """
    Validate player ID parameter.
    
    Args:
        player_id: Player ID to validate.
        
    Returns:
        Validated player ID.
        
    Raises:
        HTTPException: If validation fails.
    """
    return validate_string(player_id, "player_id", allow_empty=False)


def validate_player_name(name: Optional[str]) -> str:
    """
    Validate player name parameter.
    
    Args:
        name: Player name to validate.
        
    Returns:
        Validated player name.
        
    Raises:
        HTTPException: If validation fails.
    """
    return validate_string(name, "Player name", allow_empty=False)


def validate_emoji(emoji: Optional[str]) -> str:
    """
    Validate player emoji parameter.
    
    Args:
        emoji: Emoji to validate.
        
    Returns:
        Validated emoji.
        
    Raises:
        HTTPException: If validation fails.
    """
    return validate_string(emoji, "Player emoji", allow_empty=False)


def validate_property_id(property_id: Optional[str]) -> str:
    """
    Validate property ID parameter.
    
    Args:
        property_id: Property ID to validate.
        
    Returns:
        Validated property ID.
        
    Raises:
        HTTPException: If validation fails.
    """
    return validate_string(property_id, "property_id", allow_empty=False)


# ============================================================================
# NUMERIC VALIDATION
# ============================================================================

def validate_positive_integer(
    value: Optional[int],
    field_name: str,
    min_value: int = 0
) -> int:
    """
    Validate a positive integer parameter.
    
    Args:
        value: Integer value to validate.
        field_name: Name of field (for error messages).
        min_value: Minimum allowed value. Default: 0.
        
    Returns:
        Validated integer value.
        
    Raises:
        HTTPException: If validation fails.
    """
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required"
        )
    
    if not isinstance(value, int) or value < min_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be an integer >= {min_value}"
        )
    
    return value


# ============================================================================
# COMPOUND VALIDATION
# ============================================================================

def validate_room_join_request(
    room_id: Optional[str],
    name: Optional[str],
    emoji: Optional[str]
) -> tuple:
    """
    Validate all parameters for room join request.
    
    Args:
        room_id: Room ID.
        name: Player name.
        emoji: Player emoji.
        
    Returns:
        Tuple of validated (room_id, name, emoji).
        
    Raises:
        HTTPException: If any validation fails.
    """
    validated_room_id = validate_room_id(room_id)
    validated_name = validate_player_name(name)
    validated_emoji = validate_emoji(emoji)
    
    return (validated_room_id, validated_name, validated_emoji)
