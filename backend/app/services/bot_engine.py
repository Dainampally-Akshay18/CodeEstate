"""
Bot Engine - AI-controlled player logic for multiplayer games.

Implements decision-making for bot players following the same rules as humans:
- Must follow turn order
- Follows game rules strictly (no cheating)
- Decisions based on board state and finances
- Automatic turn execution

Phase 8: Bot System for multiplayer gameplay
"""

from typing import Dict, Any, Optional, Tuple
from app.services.game_engine import (
    roll_dice,
    move_player,
    handle_tile_action,
    get_current_player,
    is_game_over,
    next_turn,
)
from app.services.property_service import (
    buy_property,
    validate_turn,
    validate_game_state,
    get_property_by_id,
    find_player_index,
    InvalidTurnError,
    GameOverError,
)
from app.db.firebase import (
    get_room,
    update_room,
    FirebaseOperationError,
)


# ============================================================================
# CONSTANTS
# ============================================================================

LOW_MONEY_THRESHOLD = 200  # Avoid buying if money below this
MAX_BOT_TURNS_IN_SEQUENCE = 10  # Prevent infinite loops with multiple bots


# ============================================================================
# BOT DECISION ENGINE
# ============================================================================

def decide_action(game_state: Dict[str, Any], player_id: str) -> Dict[str, str]:
    """
    Decide bot's next action based on game state.
    
    Decision Logic:
    1. If player just moved to a property:
       - If unowned AND player has enough money → "buy"
       - If unowned AND low money → "skip"
       - If owned → "skip" (rent already paid)
    
    2. If player needs to pay rent/tax → "pay" (automatic)
    
    3. Default → "end_turn"
    
    Args:
        game_state: Current game state from Firebase.
        player_id: Bot player ID.
        
    Returns:
        Dict with:
        - action: "buy", "skip", "end_turn"
        - property_id: Property to buy (if action="buy"), else None
        - reason: Explanation for decision (for logging/debugging)
    """
    try:
        # Get current player
        player = None
        for p in game_state.get("players", []):
            if p["id"] == player_id:
                player = p
                break
        
        if not player:
            return {
                "action": "end_turn",
                "property_id": None,
                "reason": "Player not found in game state"
            }
        
        current_position = player["position"]
        player_money = player["money"]
        
        # Check if player landed on a property
        # For simplicity, assume positions 1-39 are properties
        # (0 is GO, 10 is JAIL, etc. - details handled by properties list)
        
        # Find property at current position
        property_at_position = _find_property_at_position(game_state, current_position)
        
        if property_at_position:
            # Check if property is owned
            if property_at_position["owner_id"] is not None:
                # Property is owned - rent already paid in handle_tile_action
                return {
                    "action": "end_turn",
                    "property_id": None,
                    "reason": f"Property {property_at_position['name']} owned by {property_at_position['owner_id']}"
                }
            
            # Property is unowned - consider buying
            property_id = property_at_position["id"]
            property_price = property_at_position["price"]
            
            # Decision: Buy if we have enough money and not low on funds
            if player_money >= property_price:
                # Check if buying would leave us with too little money
                money_after_purchase = player_money - property_price
                
                # Only buy if we keep enough cushion (LOW_MONEY_THRESHOLD)
                if money_after_purchase >= LOW_MONEY_THRESHOLD or property_price <= 100:
                    # Aggressive buying for cheap properties
                    return {
                        "action": "buy",
                        "property_id": property_id,
                        "reason": f"Buying {property_at_position['name']} (${property_price}), money left: ${money_after_purchase}"
                    }
                else:
                    return {
                        "action": "skip",
                        "property_id": None,
                        "reason": f"Low funds: ${money_after_purchase} after buying would be below threshold"
                    }
            else:
                return {
                    "action": "skip",
                    "property_id": None,
                    "reason": f"Insufficient funds: need ${property_price}, have ${player_money}"
                }
        
        # Not on a property - go to end turn
        return {
            "action": "end_turn",
            "property_id": None,
            "reason": "Player on non-property tile, ready to end turn"
        }
    
    except Exception as e:
        return {
            "action": "end_turn",
            "property_id": None,
            "reason": f"Error in decide_action: {str(e)}"
        }


def _find_property_at_position(game_state: Dict[str, Any], position: int) -> Optional[Dict[str, Any]]:
    """
    Find a property at the given board position.
    
    Note: This is a simplified implementation that assumes properties exist
    at positions corresponding to their index in the properties list.
    In a full implementation, there would be a board layout service.
    
    Args:
        game_state: Game state.
        position: Board position (0-39).
        
    Returns:
        Property dict, or None if position has no property.
    """
    # Map position to property (simplified)
    # In full implementation, use board_service to get tile at position
    
    # For now, assume:
    # - Positions with properties are where properties list maps
    # - Property #i is roughly at position (i * 10) or similar
    # - This is simplified; real implementation would use board service
    
    for prop in game_state.get("properties", []):
        # Simple heuristic: properties are typically at positions 1, 3, 5, 6, 8, 9, 11, etc.
        # For now, check if position is in a reasonable range for properties
        # (Not at GO=0, JAIL=10, Free Parking=20, Go To Jail=30)
        
        if position in [1, 3, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 21, 23, 24, 25, 26, 27, 29, 31, 32, 34, 35, 37, 39]:
            # This is a property position
            # Map position to property based on board layout
            # For simplicity, assume first property at position 1, etc.
            property_index = position // 3  # Rough mapping
            if property_index < len(game_state.get("properties", [])):
                return game_state["properties"][property_index]
    
    return None


# ============================================================================
# BOT TURN EXECUTION
# ============================================================================

def execute_bot_turn(room_id: str) -> Dict[str, Any]:
    """
    Execute a complete bot turn: roll, move, decide, act, end turn.
    
    Full flow:
    1. Fetch latest game state from Firebase
    2. Validate current player is a bot
    3. Roll dice
    4. Move player on board (handle GO rewards)
    5. Execute tile action (rent, tax, etc.)
    6. Decide next action (buy, skip, end turn)
    7. If "buy" → execute purchase
    8. Advance turn to next player
    9. Save updated state to Firebase
    10. Return updated state
    
    Args:
        room_id: Room identifier.
        
    Returns:
        Dict: Updated game_state.
        
    Raises:
        Exception: If room not found, not bot's turn, or update fails.
    """
    try:
        # Step 1: Fetch latest game state
        room = get_room(room_id)
        if not room:
            raise Exception(f"Room {room_id} not found")
        
        game_state = room.get("game_state")
        if not game_state:
            raise Exception(f"Game in room {room_id} not started")
        
        # Step 2: Validate game state and get current player
        validate_game_state(game_state)
        current_player = get_current_player(game_state)
        player_id = current_player["id"]
        
        # Validate current player is a bot
        if not current_player.get("is_bot", False):
            raise Exception(f"Player {player_id} is not a bot")
        
        # Step 3: Roll dice
        d1, d2 = roll_dice()
        total_steps = d1 + d2
        
        # Step 4: Move player
        player_idx = find_player_index(game_state, player_id)
        current_player_data = game_state["players"][player_idx]
        
        updated_player = move_player(current_player_data.copy(), total_steps)
        game_state["players"][player_idx] = updated_player
        game_state["dice"] = [d1, d2]
        
        # Step 5: Handle tile action (property, rent, tax, etc.)
        current_position = updated_player["position"]
        tile = {
            "id": current_position,
            "type": "property",
            "property_id": None
        }
        
        properties_map = {}
        for prop in game_state.get("properties", []):
            properties_map[prop["id"]] = prop
        
        game_state = handle_tile_action(
            player_idx,
            tile,
            game_state,
            properties_map
        )
        
        # Step 6: Decide action
        decision = decide_action(game_state, player_id)
        action = decision["action"]
        
        # Step 7: Execute action if needed
        if action == "buy" and decision.get("property_id"):
            try:
                game_state = buy_property(
                    game_state,
                    player_id,
                    decision["property_id"]
                )
            except Exception as e:
                # If buy fails, just continue (log for debugging)
                pass
        
        # Step 8: End turn (advance to next player)
        game_state = next_turn(game_state)
        
        # Step 9: Increment version and save to Firebase
        game_state["version"] = game_state.get("version", 1) + 1
        update_room(room_id, {"game_state": game_state})
        
        return {
            "success": True,
            "player_id": player_id,
            "dice": [d1, d2],
            "position": current_position,
            "action": action,
            "decision_reason": decision.get("reason", ""),
            "game_state": game_state
        }
    
    except Exception as e:
        raise Exception(f"Failed to execute bot turn: {str(e)}")


def execute_bot_sequence(room_id: str) -> Dict[str, Any]:
    """
    Execute consecutive bot turns until a human player or game end is reached.
    
    Handles sequences like: BOT → BOT → HUMAN (executes first 2, stops before HUMAN)
    
    Safety features:
    - Maximum iterations to prevent infinite loops
    - Respects game-over condition
    - Validates player is bot before each execution
    
    Args:
        room_id: Room identifier.
        
    Returns:
        Dict with:
        - success: bool
        - bots_executed: int (number of bot turns executed)
        - final_state: Updated game_state
        - message: Description of what happened
    """
    bots_executed = 0
    
    try:
        while bots_executed < MAX_BOT_TURNS_IN_SEQUENCE:
            # Check if game is over
            room = get_room(room_id)
            if not room:
                break
            
            game_state = room.get("game_state")
            if not game_state:
                break
            
            # Check if game has ended
            if game_state.get("phase") == "ended" or is_game_over(game_state):
                return {
                    "success": True,
                    "bots_executed": bots_executed,
                    "final_state": game_state,
                    "message": f"Game ended after {bots_executed} bot turns"
                }
            
            # Get current player
            current_player = get_current_player(game_state)
            
            # If current player is not a bot, stop
            if not current_player.get("is_bot", False):
                return {
                    "success": True,
                    "bots_executed": bots_executed,
                    "final_state": game_state,
                    "message": f"Stopped at human player {current_player['id']} after {bots_executed} bot turns"
                }
            
            # Execute bot turn
            result = execute_bot_turn(room_id)
            game_state = result["game_state"]
            bots_executed += 1
        
        # Check if we hit max iterations (safety break)
        if bots_executed >= MAX_BOT_TURNS_IN_SEQUENCE:
            return {
                "success": True,
                "bots_executed": bots_executed,
                "final_state": game_state,
                "message": f"Stopped after {bots_executed} bot turns (max iterations)"
            }
        
        return {
            "success": True,
            "bots_executed": bots_executed,
            "final_state": game_state,
            "message": f"Executed {bots_executed} bot turns successfully"
        }
    
    except Exception as e:
        return {
            "success": False,
            "bots_executed": bots_executed,
            "final_state": None,
            "message": f"Error executing bot sequence: {str(e)}"
        }
