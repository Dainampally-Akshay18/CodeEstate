"""
Game Routes - Core game action endpoints.

Handles:
- Dice rolling
- Property purchases
- Turn management
- Tile action processing
- Game state updates

Phase 7: Implements turn validation and safe updates for concurrency control.
All actions follow fetch-validate-update pattern with Firebase as source of truth.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.services.game_engine import (
    roll_dice,
    move_player,
    next_turn,
    handle_tile_action,
    get_current_player,
    is_game_over,
    get_winner,
    check_game_end,
)
from app.services.property_service import (
    buy_property,
    process_rent,
    validate_turn,
    validate_game_state,
    get_property_by_id,
    find_player_index,
    InvalidTurnError,
    InvalidPropertyError,
    PropertyOwnedError,
    InsufficientFundsError,
    GameOverError,
    PlayerBankruptError,
    StaleStateError,
)
from app.db.firebase import (
    get_room,
    update_room,
    update_room_transaction,
    FirebaseOperationError,
)
from app.services.bot_engine import execute_bot_sequence
from app.utils.cleanup import mark_game_finished
from app.utils.errors import service_exception_to_http, handle_service_exceptions
from app.utils.logging import (
    get_logger,
    log_player_action,
    log_error,
    log_game_ended,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/game", tags=["game"])
# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RollDiceRequest(BaseModel):
    """Request model for rolling dice."""
    
    room_id: str = Field(..., description="Room/game ID")
    player_id: str = Field(..., description="Player rolling dice")


class RollDiceResponse(BaseModel):
    """Response model for dice roll."""
    
    success: bool
    message: str
    dice: tuple = Field(..., description="Two dice values (d1, d2)")
    total: int
    new_position: int
    crossed_go: bool
    current_money: int
    game_state: Dict[str, Any]


class BuyPropertyRequest(BaseModel):
    """Request model for buying a property."""
    
    room_id: str = Field(..., description="Room/game ID")
    player_id: str = Field(..., description="Player attempting to buy")
    property_id: str = Field(..., description="Property to buy")


class BuyPropertyResponse(BaseModel):
    """Response model for successful property purchase."""
    
    success: bool
    message: str
    property_id: str
    price: int
    player_id: str
    remaining_money: int
    game_state: Dict[str, Any]


class ActionRequest(BaseModel):
    """Request model for handling tile actions."""
    
    room_id: str = Field(..., description="Room/game ID")
    player_id: str = Field(..., description="Player landing on tile")


class ActionResponse(BaseModel):
    """Response model for tile action execution."""
    
    success: bool
    message: str
    tile_type: str
    action_taken: Optional[Dict[str, Any]] = None
    game_state: Dict[str, Any]


class EndTurnRequest(BaseModel):
    """Request model for ending a turn."""
    
    room_id: str = Field(..., description="Room/game ID")
    player_id: str = Field(..., description="Player ending turn")


class EndTurnResponse(BaseModel):
    """Response model for turn advancement."""
    
    success: bool
    message: str
    next_player_id: str
    next_player_name: str
    game_over: bool
    winner_id: Optional[str] = None
    game_state: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    success: bool = False
    error: str
    details: Optional[str] = None


# ============================================================================
# FIREBASE DATABASE ACCESS (Phase 6-7)
# ============================================================================

def get_game_state_from_firebase(room_id: str) -> Dict[str, Any]:
    """
    Fetch latest game state from Firebase (Phase 7: Always fetch fresh).
    
    Args:
        room_id: Room ID to fetch.
        
    Returns:
        Dict: Game state from Firebase.
        
    Raises:
        HTTPException: If room or game not found.
    """
    try:
        room = get_room(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Room {room_id} not found"
            )
        
        game_state = room.get("game_state")
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game in room {room_id} hasn't started"
            )
        
        return game_state
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch game state: {str(e)}"
        )


def save_game_state_to_firebase(room_id: str, game_state: Dict[str, Any]) -> None:
    """
    Save updated game state back to Firebase (Phase 7: Safe update).
    
    Args:
        room_id: Room ID.
        game_state: Updated game state to persist.
        
    Raises:
        HTTPException: If save fails.
    """
    try:
        update_room(room_id, {"game_state": game_state})
    except FirebaseOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save game state: {str(e)}"
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/roll-dice", response_model=RollDiceResponse)
async def roll_dice_endpoint(request: RollDiceRequest) -> RollDiceResponse:
    """
    Roll dice and move player (Phase 7: Turn validation + safe update).
    
    Validation:
    - Must be player's turn
    - Player must not be bankrupt
    - Game must not be over
    
    Processing:
    1. Fetch latest game state from Firebase
    2. Validate player's turn
    3. Roll dice
    4. Move player on board
    5. Check if crossed GO
    6. Save updated state to Firebase
    
    Args:
        request: RollDiceRequest with room_id and player_id.
        
    Returns:
        RollDiceResponse with dice values, new position, and updated state.
        
    Raises:
        HTTPException: For invalid requests or game logic errors.
    """
    try:
        # Phase 7: Fetch latest state from Firebase
        game_state = get_game_state_from_firebase(request.room_id)
        
        # Phase 7: Validate turn (central validation function)
        validate_turn(game_state, request.player_id)
        
        # Roll dice
        d1, d2 = roll_dice()
        total_steps = d1 + d2
        
        # Get current player and move them
        current_player = get_current_player(game_state)
        player_idx = find_player_index(game_state, request.player_id)
        
        # Move player on board
        updated_player = move_player(current_player.copy(), total_steps)
        crossed_go = updated_player.get("money", 0) > current_player.get("money", 0)
        
        # Update game state with new position and money
        game_state["players"][player_idx] = updated_player
        game_state["dice"] = [d1, d2]
        
        # Phase 7: Increment version on update
        game_state["version"] = game_state.get("version", 1) + 1
        
        # Phase 7: Save to Firebase
        save_game_state_to_firebase(request.room_id, game_state)
        
        # Phase 10: Log player action
        log_player_action(
            request.room_id,
            request.player_id,
            "rolled_dice",
            {"dice": [d1, d2], "total": total_steps, "new_position": updated_player["position"]},
            logger
        )
        
        return RollDiceResponse(
            success=True,
            message=f"Player {request.player_id} rolled {d1}, {d2}",
            dice=(d1, d2),
            total=total_steps,
            new_position=updated_player["position"],
            crossed_go=crossed_go,
            current_money=updated_player["money"],
            game_state=game_state
        )
    
    except (InvalidTurnError, PlayerBankruptError, GameOverError) as e:
        raise service_exception_to_http(e)
    except HTTPException:
        raise
    except Exception as e:
        log_error("roll_dice", request.room_id, str(e), logger)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/buy", response_model=BuyPropertyResponse)
async def buy_property_endpoint(request: BuyPropertyRequest) -> BuyPropertyResponse:
    """
    Purchase a property (Phase 7: Turn validation + safe update).
    
    Validation (Phase 7):
    - Must be player's turn
    - Player must not be bankrupt
    - Game must not be over
    - Property must be unowned
    - Player must have funds
    
    Processing:
    1. Fetch latest game state from Firebase
    2. Validate player's turn
    3. Validate property and funds
    4. Execute purchase
    5. Increment version
    6. Save to Firebase
    
    Args:
        request: BuyPropertyRequest with room_id, player_id, property_id.
        
    Returns:
        BuyPropertyResponse with updated game state.
        
    Raises:
        HTTPException: For invalid requests or game logic errors.
    """
    try:
        # Phase 7: Fetch latest state from Firebase
        game_state = get_game_state_from_firebase(request.room_id)
        
        # Get property before purchase (for response)
        prop_before = get_property_by_id(game_state, request.property_id)
        if not prop_before:
            raise InvalidPropertyError(f"Property {request.property_id} not found")
        
        # Phase 7: Execute purchase with full validation
        game_state = buy_property(
            game_state,
            request.player_id,
            request.property_id
        )
        
        # Phase 7: Save to Firebase
        save_game_state_to_firebase(request.room_id, game_state)
        
        # Get updated player
        player_idx = find_player_index(game_state, request.player_id)
        updated_player = game_state["players"][player_idx]
        
        # Phase 10: Log player action
        log_player_action(
            request.room_id,
            request.player_id,
            "bought_property",
            {"property": prop_before['name'], "price": prop_before["price"]},
            logger
        )
        
        return BuyPropertyResponse(
            success=True,
            message=f"Player {request.player_id} successfully purchased {prop_before['name']}",
            property_id=request.property_id,
            price=prop_before["price"],
            player_id=request.player_id,
            remaining_money=updated_player["money"],
            game_state=game_state
        )
    
    except (
        InvalidTurnError,
        PlayerBankruptError,
        GameOverError,
        PropertyOwnedError,
        InsufficientFundsError,
        InvalidPropertyError,
        StaleStateError,
    ) as e:
        raise service_exception_to_http(e)
    except HTTPException:
        raise
    except Exception as e:
        log_error("buy_property", request.room_id, str(e), logger)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/action", response_model=ActionResponse)
async def handle_action_endpoint(request: ActionRequest) -> ActionResponse:
    """
    Handle tile action after player movement (Phase 7: Safe update).
    
    Processing:
    1. Fetch latest game state from Firebase
    2. Validate player is current player
    3. Get current player's tile
    4. Execute tile action (property, tax, jail, etc.)
    5. If rent needed, process rent payment
    6. Increment version
    7. Save to Firebase
    
    Args:
        request: ActionRequest with room_id and player_id.
        
    Returns:
        ActionResponse with action details and updated game state.
        
    Raises:
        HTTPException: For invalid requests or game logic errors.
    """
    try:
        # Phase 7: Fetch latest state from Firebase
        game_state = get_game_state_from_firebase(request.room_id)
        
        # Validate it's the correct player's turn
        validate_turn(game_state, request.player_id)
        
        # Get player index
        player_idx = find_player_index(game_state, request.player_id)
        if player_idx is None:
            raise InvalidPropertyError(f"Player {request.player_id} not found")
        
        player = game_state["players"][player_idx]
        current_position = player["position"]
        
        # Get tile at current position
        tile = {
            "id": current_position,
            "type": "property",
            "property_id": None
        }
        
        # Create properties map for handle_tile_action
        properties_map = {}
        for prop in game_state["properties"]:
            properties_map[prop["id"]] = prop
        
        # Execute tile action
        game_state = handle_tile_action(
            player_idx,
            tile,
            game_state,
            properties_map
        )
        
        # Check if player has an action to take (e.g., can_buy)
        action_taken = None
        if "action" in game_state["players"][player_idx]:
            action_taken = game_state["players"][player_idx]["action"]
            
            # If can_buy, process rent will be handled separately
            if action_taken.get("type") == "can_buy":
                del game_state["players"][player_idx]["action"]
        
        # Phase 7: Increment version
        game_state["version"] = game_state.get("version", 1) + 1
        
        # Phase 7: Save to Firebase
        save_game_state_to_firebase(request.room_id, game_state)
        
        # Phase 10: Log player action
        log_player_action(
            request.room_id,
            request.player_id,
            "handled_action",
            {"position": current_position, "action": action_taken},
            logger
        )
        
        return ActionResponse(
            success=True,
            message=f"Tile action processed for player {request.player_id} at position {current_position}",
            tile_type=tile["type"],
            action_taken=action_taken,
            game_state=game_state
        )
    
    except (InvalidTurnError, PlayerBankruptError, GameOverError) as e:
        raise service_exception_to_http(e)
    except HTTPException:
        raise
    except Exception as e:
        log_error("handle_action", request.room_id, str(e), logger)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing action: {str(e)}"
        )


@router.post("/end-turn", response_model=EndTurnResponse)
async def end_turn_endpoint(request: EndTurnRequest) -> EndTurnResponse:
    """
    End current player's turn and advance to next player (Phase 7: Safe update).
    
    Phase 8 Enhancement:
    - If next player is a bot, automatically execute bot sequence(s)
    - Handles consecutive bots until human player or game end reached
    
    Validation (Phase 7):
    - Must be player's turn
    - Validate before allowing end-turn
    
    Processing:
    1. Fetch latest game state from Firebase
    2. Validate it's the correct player's turn
    3. Advance to next non-bankrupt player
    4. Check if game is over
    5. Increment version and save to Firebase
    6. (Phase 8) If next player is bot, execute bot sequence
    
    Args:
        request: EndTurnRequest with room_id and player_id.
        
    Returns:
        EndTurnResponse with next player info and updated game state.
        
    Raises:
        HTTPException: For invalid requests or game logic errors.
    """
    try:
        # Phase 7: Fetch latest state from Firebase
        game_state = get_game_state_from_firebase(request.room_id)
        
        # Validate it's the correct player's turn
        validate_turn(game_state, request.player_id)
        
        # Advance to next turn
        game_state = next_turn(game_state)
        
        # Get next player info
        next_player = get_current_player(game_state)
        
        # Phase 9: Check if game should end
        game_state = check_game_end(game_state)
        
        # Phase 9: If game ended, mark as finished and set expiry
        game_over = game_state.get("phase") == "ended"
        winner_id = game_state.get("winner")
        
        # Phase 7: Increment version
        game_state["version"] = game_state.get("version", 1) + 1
        
        if game_over:
            # Mark game as finished with expiry time
            game_state = mark_game_finished(request.room_id, game_state)
            
            # Update room status to finished in Firebase
            update_room(request.room_id, {
                "status": "finished",
                "game_state": game_state
            })
            
            # Phase 10: Log game end event
            winner = next(
                (p for p in game_state["players"] if p["id"] == winner_id),
                None
            )
            if winner:
                log_game_ended(request.room_id, winner_id, winner["name"], logger)
        else:
            # Phase 7: Save to Firebase (normal turn)
            save_game_state_to_firebase(request.room_id, game_state)
            
            # Phase 10: Log turn advancement
            log_player_action(
                request.room_id,
                request.player_id,
                "ended_turn",
                {"next_player": next_player["name"]},
                logger
            )
        
        # Phase 8: If next player is a bot, execute bot turn sequence (only if game not over)
        if next_player.get("is_bot", False) and not game_over:
            try:
                bot_result = execute_bot_sequence(request.room_id)
                if bot_result.get("success"):
                    # Fetch updated state after bot sequence
                    game_state = get_game_state_from_firebase(request.room_id)
                    # Get current player after bot sequence
                    next_player = get_current_player(game_state)
            except Exception as e:
                # Bot execution error - log and continue
                log_error("execute_bot_sequence", request.room_id, str(e), logger)
        
        return EndTurnResponse(
            success=True,
            message=f"Turn advanced from {request.player_id} to {next_player['name']}",
            next_player_id=next_player["id"],
            next_player_name=next_player["name"],
            game_over=game_over,
            winner_id=winner_id,
            game_state=game_state
        )
    
    except (InvalidTurnError, PlayerBankruptError, GameOverError) as e:
        raise service_exception_to_http(e)
    except HTTPException:
        raise
    except IndexError:
        log_error("end_turn", request.room_id, "No valid next player", logger)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid next player (all players bankrupt?)"
        )
    except Exception as e:
        log_error("end_turn", request.room_id, str(e), logger)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ending turn: {str(e)}"
        )


# ============================================================================
# BOT DEBUG ENDPOINTS (Phase 8)
# ============================================================================

class ExecuteBotSequenceRequest(BaseModel):
    """Request to manually execute bot sequence."""
    
    room_id: str = Field(..., description="Room/game ID")


@router.post("/bot/execute-sequence")
async def execute_bot_sequence_debug(request: ExecuteBotSequenceRequest) -> Dict[str, Any]:
    """
    DEBUG ENDPOINT: Manually execute bot turn sequence (Phase 8).
    
    Used for testing/debugging bot logic. In production, bots are automatically
    triggered when a human player ends their turn.
    
    Args:
        request: ExecuteBotSequenceRequest with room_id.
        
    Returns:
        Dict with:
        - success: bool
        - bots_executed: number of bot turns executed
        - final_state: Updated game state
        - message: Description
        
    Raises:
        HTTPException: If room not found or sequence fails.
    """
    try:
        result = execute_bot_sequence(request.room_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute bot sequence: {str(e)}"
        )


# ============================================================================
# CLEANUP ENDPOINTS (Phase 9)
# ============================================================================

class CleanupRequest(BaseModel):
    """Request to manually trigger cleanup."""
    pass


@router.post("/cleanup")
async def cleanup_expired_games_debug() -> Dict[str, Any]:
    """
    DEBUG ENDPOINT: Manually trigger cleanup of expired games (Phase 9).
    
    Scans Firebase for finished games that have expired (10 minutes old)
    and deletes them. Runs automatically in production background.
    
    Returns:
        Dict with:
        - success: bool
        - games_deleted: int (number of games deleted)
        - errors: List of error messages (if any)
        - message: Summary
        
    Raises:
        HTTPException: If cleanup encounters fatal errors.
    """
    try:
        from app.utils.cleanup import cleanup_expired_games
        result = cleanup_expired_games()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )
