"""
Room Routes - Multiplayer room management endpoints.

Handles:
- Room creation
- Player joining
- Game initialization
- Room state queries

Phase 10: Added logging and centralized error handling
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from app.services.room_service import (
    create_room,
    get_room,
    get_game_state,
    join_room,
    start_game,
    get_room_players,
    get_player_count,
    is_room_full,
    is_game_started,
    RoomServiceError,
    RoomNotFoundError,
    RoomFullError,
    GameAlreadyStartedError,
    InsufficientPlayersError,
    InvalidGameStateError,
)
from app.utils.logging import (
    get_logger,
    log_room_created,
    log_player_joined,
    log_game_started,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/room", tags=["room"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateRoomResponse(BaseModel):
    """Response for room creation."""
    
    success: bool
    room_id: str
    message: str


class PlayerJoinData(BaseModel):
    """Player data for joining."""
    
    id: str
    name: str
    emoji: str
    position: int = 0
    money: int = 1500
    properties: List[str] = []
    is_bot: bool = False
    is_bankrupt: bool = False


class JoinRoomRequest(BaseModel):
    """Request model for joining a room."""
    
    room_id: str = Field(..., description="Room to join")
    name: str = Field(..., description="Player name")
    emoji: str = Field(..., description="Player emoji")
    is_bot: bool = Field(default=False, description="Is bot player")


class JoinRoomResponse(BaseModel):
    """Response for successful room join."""
    
    success: bool
    message: str
    room_id: str
    player_id: str
    player_count: int
    players: List[Dict[str, Any]]


class StartGameRequest(BaseModel):
    """Request model for starting game."""
    
    room_id: str = Field(..., description="Room to start game in")


class StartGameResponse(BaseModel):
    """Response for game start."""
    
    success: bool
    message: str
    room_id: str
    game_state: Dict[str, Any]


class RoomDetailsResponse(BaseModel):
    """Response for room details."""
    
    success: bool
    room_id: str
    status: str
    player_count: int
    max_players: int = 6
    players: List[Dict[str, Any]]
    created_at: str
    game_started: bool


class GameStateResponse(BaseModel):
    """Response for game state."""
    
    success: bool
    game_state: Dict[str, Any]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/create", response_model=CreateRoomResponse)
async def create_room_endpoint() -> CreateRoomResponse:
    """
    Create a new game room.
    
    Phase 10: Logs room creation event.
    
    Returns:
        CreateRoomResponse with new room ID.
    """
    try:
        room = create_room()
        
        # Phase 10: Log room creation
        log_room_created(room["room_id"], 6, logger)
        
        return CreateRoomResponse(
            success=True,
            room_id=room["room_id"],
            message=f"Room {room['room_id']} created successfully"
        )
    
    except RoomServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/join", response_model=JoinRoomResponse)
async def join_room_endpoint(request: JoinRoomRequest) -> JoinRoomResponse:
    """
    Join an existing room as a player.
    
    Validation:
    - Room must exist
    - Room must not be full
    - Room must not have started
    
    Phase 10: Logs player join event.
    
    Args:
        request: JoinRoomRequest with room_id, name, emoji.
        
    Returns:
        JoinRoomResponse with updated player count and room details.
        
    Raises:
        HTTPException: For various validation errors.
    """
    try:
        # Validate inputs
        if not request.room_id or not request.room_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="room_id cannot be empty"
            )
        
        if not request.name or not request.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player name cannot be empty"
            )
        
        if not request.emoji or not request.emoji.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player emoji cannot be empty"
            )
        
        # Join room
        updated_room = join_room(
            request.room_id,
            request.name,
            request.emoji,
            request.is_bot
        )
        
        # Get player ID of newly joined player
        new_player = updated_room["players"][-1]
        
        # Phase 10: Log player join
        log_player_joined(request.room_id, new_player["id"], request.name, logger)
        
        return JoinRoomResponse(
            success=True,
            message=f"{request.name} joined room {request.room_id}",
            room_id=request.room_id,
            player_id=new_player["id"],
            player_count=len(updated_room["players"]),
            players=updated_room["players"]
        )
    
    except RoomNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RoomFullError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except GameAlreadyStartedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining room: {str(e)}"
        )


@router.post("/start", response_model=StartGameResponse)
async def start_game_endpoint(request: StartGameRequest) -> StartGameResponse:
    """
    Initialize and start the game in a room.
    
    Validation:
    - Room must exist
    - Room must have 2-6 players
    
    Phase 10: Logs game start event.
    
    Args:
        request: StartGameRequest with room_id.
        
    Returns:
        StartGameResponse with initialized GameState.
        
    Raises:
        HTTPException: For validation or game logic errors.
    """
    try:
        if not request.room_id or not request.room_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="room_id cannot be empty"
            )
        
        # Start game
        game_state = start_game(request.room_id)
        
        # Phase 10: Log game start
        log_game_started(request.room_id, len(game_state['players']), logger)
        
        return StartGameResponse(
            success=True,
            message=f"Game in room {request.room_id} started with {len(game_state['players'])} players",
            room_id=request.room_id,
            game_state=game_state
        )
    
    except RoomNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InsufficientPlayersError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting game: {str(e)}"
        )


@router.get("/{room_id}", response_model=RoomDetailsResponse)
async def get_room_endpoint(room_id: str) -> RoomDetailsResponse:
    """
    Get details of a specific room.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        RoomDetailsResponse with room info and player list.
        
    Raises:
        HTTPException: If room not found.
    """
    try:
        room = get_room(room_id)
        
        return RoomDetailsResponse(
            success=True,
            room_id=room["room_id"],
            status=room["status"],
            player_count=len(room["players"]),
            players=room["players"],
            created_at=room["created_at"],
            game_started=room["status"] == "playing"
        )
    
    except RoomNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching room: {str(e)}"
        )


@router.get("/{room_id}/state", response_model=GameStateResponse)
async def get_game_state_endpoint(room_id: str) -> GameStateResponse:
    """
    Get current game state in a room.
    
    Args:
        room_id: Room identifier.
        
    Returns:
        GameStateResponse with current game state.
        
    Raises:
        HTTPException: If room not found or game not started.
    """
    try:
        game_state = get_game_state(room_id)
        
        return GameStateResponse(
            success=True,
            game_state=game_state
        )
    
    except RoomNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidGameStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching game state: {str(e)}"
        )


# ============================================================================
# DEBUG ENDPOINTS (Phase 5 only, remove in Phase 6+)
# ============================================================================

@router.get("", tags=["debug"])
async def list_rooms_endpoint() -> Dict[str, Any]:
    """
    DEBUG ENDPOINT: List all active rooms (temporary).
    
    This will be removed when Firebase integration is added.
    
    Returns:
        Dict: Summary of all rooms.
    """
    from app.services.room_service import list_all_rooms
    
    rooms = list_all_rooms()
    return {
        "success": True,
        "total_rooms": len(rooms),
        "rooms": rooms
    }
