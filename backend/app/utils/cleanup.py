"""
Cleanup Utilities - Handle expired game cleanup and maintenance.

Manages deletion of finished games from Firebase after expiry period.
Ensures system doesn't accumulate unnecessary data.

Phase 9: Game End + Cleanup
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.db.firebase import (
    query_collection,
    delete_document,
    FirebaseOperationError,
)


# ============================================================================
# CONSTANTS
# ============================================================================

GAME_EXPIRY_MINUTES = 10  # Keep finished games for 10 minutes
GAMES_COLLECTION = "rooms"


# ============================================================================
# CLEANUP FUNCTIONS
# ============================================================================

def get_expiry_time(minutes: int = GAME_EXPIRY_MINUTES) -> str:
    """
    Calculate expiry timestamp (current time + specified minutes).
    
    Args:
        minutes: Minutes to add to current time. Default: GAME_EXPIRY_MINUTES.
        
    Returns:
        str: ISO format timestamp (e.g., "2026-04-16T12:34:56.789123")
    """
    expiry = datetime.utcnow() + timedelta(minutes=minutes)
    return expiry.isoformat()


def mark_game_finished(room_id: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark a game as finished and set expiry time in game state.
    
    Called when:
    - Only 1 player remains (winner determined)
    - Game is declared ended
    
    Updates game_state with:
    - phase: "ended" (if not already set)
    - winner: winning player ID
    - expires_at: ISO timestamp when room should be deleted
    
    Args:
        room_id: Room identifier.
        game_state: Game state to mark as finished.
        
    Returns:
        Dict: Updated game_state with end markers.
    """
    if game_state.get("phase") != "ended":
        game_state["phase"] = "ended"
    
    # Set expiry time if not already set
    if not game_state.get("expires_at"):
        game_state["expires_at"] = get_expiry_time()
    
    return game_state


def cleanup_expired_games() -> Dict[str, Any]:
    """
    Scan Firebase and delete all expired finished games.
    
    Process:
    1. Query all rooms with status="finished" AND expires_at < current_time
    2. Delete each expired room document
    3. Return cleanup statistics
    
    Safety Features:
    - Only deletes documents with status="finished"
    - Only deletes if expires_at is in the past
    - Skips documents without expires_at field
    - Continues on individual deletion failures
    - Logs errors but doesn't break
    
    Returns:
        Dict with:
        - success: bool (true if no fatal errors)
        - games_deleted: int (number of games deleted)
        - errors: List of error messages (if any)
        - message: Human-readable summary
        
    Raises:
        None (catches and reports all exceptions)
    """
    errors = []
    games_deleted = 0
    
    try:
        current_time = datetime.utcnow()
        
        # Query all rooms with status="finished"
        try:
            finished_rooms = query_collection(
                GAMES_COLLECTION,
                where_clause=("status", "==", "finished")
            )
        except FirebaseOperationError as e:
            errors.append(f"Failed to query finished rooms: {str(e)}")
            return {
                "success": False,
                "games_deleted": 0,
                "errors": errors,
                "message": f"Cleanup failed: {errors[0]}"
            }
        
        # Check each room for expiry
        for room in finished_rooms:
            room_id = room.get("room_id")
            expires_at_str = room.get("expires_at")
            
            if not room_id or not expires_at_str:
                continue
            
            # Parse expiry time
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"Invalid expiry format for room {room_id}: {expires_at_str}")
                continue
            
            # Check if expired
            if expires_at < current_time:
                # Delete room
                try:
                    delete_document(GAMES_COLLECTION, room_id)
                    games_deleted += 1
                except FirebaseOperationError as e:
                    errors.append(f"Failed to delete room {room_id}: {str(e)}")
                    continue
        
        return {
            "success": True,
            "games_deleted": games_deleted,
            "errors": errors,
            "message": f"Cleanup completed: {games_deleted} games deleted"
        }
    
    except Exception as e:
        return {
            "success": False,
            "games_deleted": games_deleted,
            "errors": [str(e)],
            "message": f"Cleanup failed with unexpected error: {str(e)}"
        }


def validate_game_not_ended(game_state: Dict[str, Any]) -> bool:
    """
    Check if game is still active (not ended).
    
    Args:
        game_state: Game state to check.
        
    Returns:
        bool: True if game is not ended, False if ended.
    """
    return game_state.get("phase") != "ended"
