"""
Room Service - Business logic for room management and multiplayer setup.

Handles room creation, player joining, and game initialization.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models.player import Player
from app.models.game_state import GameState, GamePhase
from app.models.room import Room, RoomStatus


# ============================================================================
# IN-MEMORY STORAGE (TEMPORARY - will be replaced by Firebase in Phase 6)
# ============================================================================

ROOMS: Dict[str, Dict[str, Any]] = {}

# Maximum players per room
MAX_PLAYERS = 6
MIN_PLAYERS = 2

# Default starting money for players
STARTING_MONEY = 1500


# ============================================================================
# EXCEPTIONS
# ============================================================================

class RoomServiceError(Exception):
    """Base exception for room service errors."""
    pass


class RoomNotFoundError(RoomServiceError):
    """Raised when room doesn't exist."""
    pass


class RoomFullError(RoomServiceError):
    """Raised when attempting to join a full room."""
    pass


class InvalidGameStateError(RoomServiceError):
    """Raised when game state is invalid."""
    pass


class GameAlreadyStartedError(RoomServiceError):
    """Raised when attempting to join a room that already started."""
    pass


class InsufficientPlayersError(RoomServiceError):
    """Raised when attempting to start game with too few players."""
    pass


# ============================================================================
# BOARD INITIALIZATION
# ============================================================================

def _initialize_properties() -> List[Dict[str, Any]]:
    """
    Initialize board properties (Tech companies).
    
    Returns:
        List: Basic property list for the board.
    """
    properties = [
        {
            "id": "prop_1",
            "name": "Google",
            "price": 60,
            "rent_levels": [2, 10, 30, 90, 160, 250],
            "color_group": "brown",
            "owner_id": None,
            "houses": 0,
            "has_hotel": False,
        },
        {
            "id": "prop_2",
            "name": "Apple",
            "price": 60,
            "rent_levels": [4, 20, 60, 180, 320, 450],
            "color_group": "brown",
            "owner_id": None,
            "houses": 0,
            "has_hotel": False,
        },
        {
            "id": "prop_3",
            "name": "Microsoft",
            "price": 100,
            "rent_levels": [6, 30, 90, 270, 400, 550],
            "color_group": "blue",
            "owner_id": None,
            "houses": 0,
            "has_hotel": False,
        },
        {
            "id": "prop_4",
            "name": "Tesla",
            "price": 100,
            "rent_levels": [8, 40, 100, 300, 450, 600],
            "color_group": "blue",
            "owner_id": None,
            "houses": 0,
            "has_hotel": False,
        },
        {
            "id": "prop_5",
            "name": "Amazon",
            "price": 120,
            "rent_levels": [10, 50, 150, 450, 625, 750],
            "color_group": "red",
            "owner_id": None,
            "houses": 0,
            "has_hotel": False,
        },
        {
            "id": "prop_6",
            "name": "Meta",
            "price": 120,
            "rent_levels": [12, 60, 180, 500, 700, 900],
            "color_group": "red",
            "owner_id": None,
            "houses": 0,
            "has_hotel": False,
        },
    ]
    return properties


# ============================================================================
# ROOM MANAGEMENT
# ============================================================================

def create_room() -> Dict[str, Any]:
    """
    Create a new game room.
    
    Generates a unique room ID, initializes empty player list,
    and sets status to "waiting".
    
    Returns:
        Dict: Room object with id, players, status, created_at.
        
    Raises:
        RoomServiceError: If room creation fails.
    """
    try:
        room_id = str(uuid.uuid4())[:8].upper()  # 8-char uppercase ID
        
        room = {
            "room_id": room_id,
            "status": "waiting",
            "players": [],
            "game_state": None,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": None,
        }
        
        ROOMS[room_id] = room
        return room
    
    except Exception as e:
        raise RoomServiceError(f"Failed to create room: {str(e)}")


def get_room(room_id: str) -> Dict[str, Any]:
    """
    Retrieve a room by ID.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        Dict: Room object.
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
    """
    if room_id not in ROOMS:
        raise RoomNotFoundError(f"Room {room_id} not found")
    
    return ROOMS[room_id]


def get_game_state(room_id: str) -> Dict[str, Any]:
    """
    Retrieve game state from a room.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        Dict: GameState object.
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
        InvalidGameStateError: If game hasn't started.
    """
    room = get_room(room_id)
    
    if not room["game_state"]:
        raise InvalidGameStateError(f"Game in room {room_id} hasn't started yet")
    
    return room["game_state"]


# ============================================================================
# PLAYER JOINING
# ============================================================================

def join_room(
    room_id: str,
    player_name: str,
    emoji: str,
    is_bot: bool = False
) -> Dict[str, Any]:
    """
    Add a player to an existing room.
    
    Validation:
    - Room must exist
    - Room must not be full (max 6 players)
    - Room must not have started
    - Player name and emoji must be provided
    
    Args:
        room_id: Room to join.
        player_name: Player's display name.
        emoji: Player's emoji representation.
        is_bot: Whether this player is AI-controlled.
        
    Returns:
        Dict: Updated room object with new player added.
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
        RoomFullError: If room is at max capacity.
        GameAlreadyStartedError: If game has started.
    """
    # Validate room exists
    room = get_room(room_id)
    
    # Validate room hasn't started
    if room["status"] != "waiting":
        raise GameAlreadyStartedError(
            f"Cannot join room {room_id}: game has already started"
        )
    
    # Validate room isn't full
    if len(room["players"]) >= MAX_PLAYERS:
        raise RoomFullError(
            f"Room {room_id} is full (max {MAX_PLAYERS} players)"
        )
    
    # Validate inputs
    if not player_name or not player_name.strip():
        raise ValueError("Player name cannot be empty")
    if not emoji or not emoji.strip():
        raise ValueError("Emoji cannot be empty")
    
    # Create player
    player_id = f"player_{len(room['players']) + 1}"
    
    player = {
        "id": player_id,
        "name": player_name.strip(),
        "emoji": emoji.strip(),
        "position": 0,
        "money": STARTING_MONEY,
        "properties": [],
        "is_bot": is_bot,
        "is_bankrupt": False,
    }
    
    # Add to room
    room["players"].append(player)
    
    return room


# ============================================================================
# GAME INITIALIZATION
# ============================================================================

def start_game(room_id: str) -> Dict[str, Any]:
    """
    Initialize and start the game in a room.
    
    Validation:
    - Room must exist
    - Room must have 2-6 players
    
    Initialization:
    - Create GameState with all players
    - Set initial positions to 0
    - Set starting money to 1500 each
    - Initialize properties
    - Set current_turn to 0
    - Set phase to "rolling"
    
    Args:
        room_id: Room to start game in.
        
    Returns:
        Dict: GameState object.
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
        InsufficientPlayersError: If fewer than 2 players.
    """
    # Validate room exists
    room = get_room(room_id)
    
    # Validate player count
    num_players = len(room["players"])
    if num_players < MIN_PLAYERS:
        raise InsufficientPlayersError(
            f"Cannot start game: need at least {MIN_PLAYERS} players, "
            f"but only {num_players} in room"
        )
    
    # Convert players to dicts (ensure proper format)
    players_data = []
    for player in room["players"]:
        players_data.append({
            "id": player["id"],
            "name": player["name"],
            "emoji": player["emoji"],
            "position": 0,
            "money": STARTING_MONEY,
            "properties": [],
            "is_bot": player.get("is_bot", False),
            "is_bankrupt": False,
        })
    
    # Initialize properties
    properties_data = _initialize_properties()
    
    # Create game state
    game_state = {
        "room_id": room_id,
        "players": players_data,
        "properties": properties_data,
        "current_turn": 0,
        "dice": [0, 0],
        "phase": "rolling",
        "winner": None,
        "version": 1,  # Phase 7: State versioning for concurrency control
    }
    
    # Attach to room and update status
    room["game_state"] = game_state
    room["status"] = "playing"
    
    return game_state


# ============================================================================
# ROOM STATE UTILITIES
# ============================================================================

def get_room_players(room_id: str) -> List[Dict[str, Any]]:
    """
    Get all players in a room.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        List: Player objects in the room.
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
    """
    room = get_room(room_id)
    return room["players"]


def get_player_count(room_id: str) -> int:
    """
    Get number of players in a room.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        int: Number of players.
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
    """
    room = get_room(room_id)
    return len(room["players"])


def is_room_full(room_id: str) -> bool:
    """
    Check if a room is at maximum capacity.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        bool: True if room has MAX_PLAYERS players.
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
    """
    return get_player_count(room_id) >= MAX_PLAYERS


def is_game_started(room_id: str) -> bool:
    """
    Check if game has started in a room.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        bool: True if room status is "playing".
        
    Raises:
        RoomNotFoundError: If room doesn't exist.
    """
    room = get_room(room_id)
    return room["status"] == "playing"


def list_all_rooms() -> List[Dict[str, Any]]:
    """
    Get all active rooms (for debugging/admin).
    
    Returns:
        List: All room objects.
    """
    return list(ROOMS.values())
