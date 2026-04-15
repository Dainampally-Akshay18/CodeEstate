"""
Logging Utilities - Centralized logging configuration.

Provides consistent logging for important events:
- Room creation and management
- Game start/end transitions
- Error tracking
- Action logging

Phase 10: Production-Ready Logging
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps


# ============================================================================
# LOGGER SETUP
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__).
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


# ============================================================================
# GAME EVENT LOGGING
# ============================================================================

def log_room_created(room_id: str, max_players: int, logger: Optional[logging.Logger] = None):
    """
    Log room creation event.
    
    Args:
        room_id: Room ID created.
        max_players: Maximum players allowed in room.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Room created: {room_id} (max_players={max_players})")


def log_player_joined(room_id: str, player_id: str, player_name: str, logger: Optional[logging.Logger] = None):
    """
    Log player joining room.
    
    Args:
        room_id: Room ID.
        player_id: Player ID.
        player_name: Player name.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Player joined: {room_id} -> {player_name} ({player_id})")


def log_game_started(room_id: str, player_count: int, logger: Optional[logging.Logger] = None):
    """
    Log game start event.
    
    Args:
        room_id: Room ID.
        player_count: Number of players.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Game started: {room_id} with {player_count} players")


def log_game_ended(room_id: str, winner_id: str, winner_name: str, logger: Optional[logging.Logger] = None):
    """
    Log game end event.
    
    Args:
        room_id: Room ID.
        winner_id: Winner's player ID.
        winner_name: Winner's name.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Game ended: {room_id} - Winner: {winner_name} ({winner_id})")


def log_player_action(
    room_id: str,
    player_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
):
    """
    Log player action event.
    
    Args:
        room_id: Room ID.
        player_id: Player ID performing action.
        action: Action type (e.g., "rolled_dice", "bought_property", "ended_turn").
        details: Optional action details dict.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    detail_str = ""
    if details:
        detail_str = f" | {details}"
    
    logger.info(f"{room_id} - {player_id} - {action}{detail_str}")


def log_error(
    component: str,
    room_id: str,
    error_msg: str,
    logger: Optional[logging.Logger] = None
):
    """
    Log error event.
    
    Args:
        component: Component/service where error occurred.
        room_id: Room ID (if applicable).
        error_msg: Error message.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.error(f"{component} [{room_id}]: {error_msg}")


def log_cleanup(games_deleted: int, errors: int, logger: Optional[logging.Logger] = None):
    """
    Log cleanup event.
    
    Args:
        games_deleted: Number of games deleted.
        errors: Number of errors during cleanup.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Cleanup completed: {games_deleted} games deleted, {errors} errors")


# ============================================================================
# PERFORMANCE LOGGING
# ============================================================================

def log_operation_timing(operation_name: str, duration_ms: float, logger: Optional[logging.Logger] = None):
    """
    Log operation timing for performance monitoring.
    
    Args:
        operation_name: Name of operation.
        duration_ms: Duration in milliseconds.
        logger: Logger instance (optional).
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.debug(f"{operation_name} completed in {duration_ms:.2f}ms")


def timed_operation(operation_name: str, logger: Optional[logging.Logger] = None):
    """
    Decorator to log operation timing.
    
    Usage:
        @timed_operation("fetch_game_state")
        def my_function():
            ...
    
    Args:
        operation_name: Name of operation for logging.
        logger: Logger instance (optional).
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = (time.time() - start) * 1000
                log_operation_timing(operation_name, duration, logger)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.time() - start) * 1000
                log_operation_timing(operation_name, duration, logger)
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
