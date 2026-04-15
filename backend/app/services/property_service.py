"""
Property Service - Business logic for property transactions.

Handles property purchases, rent calculations, and property-related operations.
Implements turn validation and safe state updates for concurrent access.
"""

from typing import Dict, Any, Optional
from app.services.game_engine import calculate_rent, pay_rent, get_current_player, is_game_over


class PropertyServiceError(Exception):
    """Base exception for property service errors."""
    pass


class InvalidPropertyError(PropertyServiceError):
    """Raised when property doesn't exist or is invalid."""
    pass


class PropertyOwnedError(PropertyServiceError):
    """Raised when attempting to buy an already-owned property."""
    pass


class InsufficientFundsError(PropertyServiceError):
    """Raised when player doesn't have enough money to buy property."""
    pass


class InvalidTurnError(PropertyServiceError):
    """Raised when attempting action on wrong player's turn."""
    pass


class GameOverError(PropertyServiceError):
    """Raised when attempting action in a ended game."""
    pass


class PlayerBankruptError(PropertyServiceError):
    """Raised when attempting action with bankrupt player."""
    pass


class StaleStateError(PropertyServiceError):
    """Raised when game state version doesn't match (concurrent update detected)."""
    pass


# ============================================================================
# CENTRAL TURN VALIDATION (Phase 7)
# ============================================================================

def validate_turn(game_state: Dict[str, Any], player_id: str) -> None:
    """
    Validate that it is the specified player's turn and game is not over.
    
    This is the central validation function used before ANY player action.
    
    Checks:
    1. Game is not ended
    2. Player is the current player
    3. Player is not bankrupt
    
    Args:
        game_state: GameState dict.
        player_id: Player attempting action.
        
    Raises:
        GameOverError: If game has ended.
        InvalidTurnError: If wrong player or player bankrupt.
        PlayerBankruptError: If player is bankrupt.
    """
    # Check game not ended
    if game_state.get("phase") == "ended":
        raise GameOverError("Game has ended. No more actions allowed.")
    
    if is_game_over(game_state):
        raise GameOverError("Game has ended. No more actions allowed.")
    
    # Get current player
    current_player = get_current_player(game_state)
    
    # Check if wrong player
    if current_player["id"] != player_id:
        raise InvalidTurnError(
            f"It is not {player_id}'s turn. Current turn: {current_player['id']}"
        )
    
    # Check if player is bankrupt
    if current_player.get("is_bankrupt", False):
        raise PlayerBankruptError(
            f"Player {player_id} is bankrupt and cannot take actions."
        )


def validate_game_state(game_state: Dict[str, Any]) -> None:
    """
    Validate that the game state is in a valid state for actions.
    
    Checks:
    1. Game has started (has players and properties)
    2. Game is not ended
    
    Args:
        game_state: GameState dict.
        
    Raises:
        GameOverError: If game has ended.
        PropertyServiceError: If game state is invalid.
    """
    if not game_state:
        raise PropertyServiceError("Game state is empty or not found.")
    
    if not game_state.get("players"):
        raise PropertyServiceError("Game state missing players.")
    
    if not game_state.get("properties"):
        raise PropertyServiceError("Game state missing properties.")
    
    if game_state.get("phase") == "ended":
        raise GameOverError("Game has ended.")


# ============================================================================
# PROPERTY QUERIES
# ============================================================================

def get_property_by_id(game_state: Dict[str, Any], property_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a property from game_state by its ID.
    
    Args:
        game_state: GameState dict.
        property_id: Property ID to look up.
        
    Returns:
        Dict: Property dict, or None if not found.
    """
    for prop in game_state["properties"]:
        if prop["id"] == property_id:
            return prop
    return None


def get_player_by_id(game_state: Dict[str, Any], player_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a player from game_state by their ID.
    
    Args:
        game_state: GameState dict.
        player_id: Player ID to look up.
        
    Returns:
        Dict: Player dict, or None if not found.
    """
    for player in game_state["players"]:
        if player["id"] == player_id:
            return player
    return None


def find_player_index(game_state: Dict[str, Any], player_id: str) -> Optional[int]:
    """
    Find the index of a player in game_state.players.
    
    Args:
        game_state: GameState dict.
        player_id: Player ID to find.
        
    Returns:
        int: Player index, or None if not found.
    """
    for idx, player in enumerate(game_state["players"]):
        if player["id"] == player_id:
            return idx
    return None


# ============================================================================
# PROPERTY PURCHASE
# ============================================================================

def buy_property(
    game_state: Dict[str, Any],
    player_id: str,
    property_id: str,
    expected_version: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute property purchase logic with turn validation and version checking.
    
    Validation (Phase 7 - Safe Updates):
    - It must be the player's turn (validate_turn)
    - Player is not bankrupt
    - Game is not over
    - Property must exist and be unowned
    - Player must have enough money
    - State version matches (prevent stale updates) - OPTIONAL
    
    Updates:
    - Deducts property price from player's money
    - Sets owner_id on property
    - Adds property to player's properties list
    - Increments game_state version number
    
    Args:
        game_state: GameState dict (must be fresh from Firebase).
        player_id: Player attempting to buy.
        property_id: Property to purchase.
        expected_version: Optional version number to detect concurrent updates.
        
    Returns:
        Dict: Updated game_state with version incremented.
        
    Raises:
        InvalidTurnError: If not player's turn or player is bankrupt.
        GameOverError: If game has ended.
        InvalidPropertyError: If property doesn't exist.
        PropertyOwnedError: If property is already owned.
        InsufficientFundsError: If player lacks funds.
        StaleStateError: If state version doesn't match (concurrent update detected).
    """
    # Phase 7: Validate game state (fresh from Firebase)
    validate_game_state(game_state)
    
    # Phase 7: Check for concurrent updates
    if expected_version is not None:
        current_version = game_state.get("version", 1)
        if current_version != expected_version:
            raise StaleStateError(
                f"Game state was modified by another player. "
                f"Expected version {expected_version}, got {current_version}. "
                f"Please fetch latest state and retry."
            )
    
    # Phase 7: Validate it's the player's turn and not bankrupt
    validate_turn(game_state, player_id)
    
    # Find property
    property_obj = get_property_by_id(game_state, property_id)
    if not property_obj:
        raise InvalidPropertyError(f"Property {property_id} not found")
    
    # Validate property is unowned
    if property_obj["owner_id"] is not None:
        raise PropertyOwnedError(
            f"Property {property_id} already owned by {property_obj['owner_id']}"
        )
    
    # Get current player (already validated by validate_turn)
    current_player = get_current_player(game_state)
    
    # Validate player has enough money
    if current_player["money"] < property_obj["price"]:
        raise InsufficientFundsError(
            f"Player {player_id} has ${current_player['money']}, "
            f"but property costs ${property_obj['price']}"
        )
    
    # Execute purchase (safe in-memory update)
    player_idx = find_player_index(game_state, player_id)
    
    # Deduct money from player
    game_state["players"][player_idx]["money"] -= property_obj["price"]
    
    # Find property index and set owner
    for prop in game_state["properties"]:
        if prop["id"] == property_id:
            prop["owner_id"] = player_id
            break
    
    # Add property to player's list
    game_state["players"][player_idx]["properties"].append(property_id)
    
    # Phase 7: Increment version after successful update
    game_state["version"] = game_state.get("version", 1) + 1
    
    return game_state


# ============================================================================
# RENT PROCESSING
# ============================================================================

def process_rent(
    game_state: Dict[str, Any],
    player_id: str,
    property_id: str
) -> Dict[str, Any]:
    """
    Process rent payment for a property (safe update).
    
    If property has an owner different from the player:
    - Calculates rent based on the property's improvements
    - Deducts rent from player
    - Adds rent to owner
    - Marks player bankrupt if money goes negative
    - Increments game_state version
    
    Args:
        game_state: GameState dict (must be fresh from Firebase).
        player_id: Player landing on property.
        property_id: Property where rent is due.
        
    Returns:
        Dict: Updated game_state with version incremented.
        
    Raises:
        InvalidPropertyError: If property doesn't exist.
    """
    # Find property
    property_obj = get_property_by_id(game_state, property_id)
    if not property_obj:
        raise InvalidPropertyError(f"Property {property_id} not found")
    
    # If property is unowned or owned by player, no rent
    if not property_obj["owner_id"] or property_obj["owner_id"] == player_id:
        return game_state
    
    # Find player and owner
    player_idx = find_player_index(game_state, player_id)
    owner_idx = find_player_index(game_state, property_obj["owner_id"])
    
    if player_idx is None or owner_idx is None:
        raise InvalidPropertyError(
            f"Player {player_id} or owner {property_obj['owner_id']} not found"
        )
    
    # Calculate and process rent
    rent_amount = calculate_rent(property_obj)
    
    payer = game_state["players"][player_idx]
    receiver = game_state["players"][owner_idx]
    
    payer, receiver = pay_rent(payer, receiver, rent_amount)
    
    game_state["players"][player_idx] = payer
    game_state["players"][owner_idx] = receiver
    
    # Phase 7: Increment version after successful update
    game_state["version"] = game_state.get("version", 1) + 1
    
    return game_state


# ============================================================================
# PROPERTY UPGRADES (Phase 5+)
# ============================================================================
# Placeholder for future implementation:
# - build_house()
# - build_hotel()
# - remove_house()
# These will be added in a later phase.
