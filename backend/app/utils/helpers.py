"""
Helper utilities for common operations.
Used across services and routes.
"""

import time
from typing import Tuple


def get_current_timestamp() -> float:
    """
    Get current timestamp in seconds.
    
    Returns:
        float: Current Unix timestamp
    """
    return time.time()


def add_seconds_to_timestamp(timestamp: float, seconds: int) -> float:
    """
    Add seconds to a timestamp.
    
    Args:
        timestamp: Base timestamp
        seconds: Seconds to add
        
    Returns:
        float: New timestamp
    """
    return timestamp + seconds


def generate_room_code(length: int = 6) -> str:
    """
    Generate a random room code.
    
    Args:
        length: Length of room code
        
    Returns:
        str: Random alphanumeric room code
    """
    import random
    import string

    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def validate_player_count(count: int) -> bool:
    """
    Validate if player count is within allowed range.
    
    Args:
        count: Number of players
        
    Returns:
        bool: True if valid (2-6 players), False otherwise
    """
    MIN_PLAYERS = 2
    MAX_PLAYERS = 6
    return MIN_PLAYERS <= count <= MAX_PLAYERS
