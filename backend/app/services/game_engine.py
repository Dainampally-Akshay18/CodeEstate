"""
Game Engine - Core game logic for Tech Monopoly.

This module contains all deterministic, pure game logic functions.
No database calls or Firebase integration here - all logic is testable and reusable.
"""

import random
from typing import Tuple, Dict, Any, List
from app.models.player import Player
from app.models.property import Property
from app.models.tile import Tile, TileType
from app.models.game_state import GameState


# ============================================================================
# CONSTANTS
# ============================================================================

BOARD_SIZE = 40
GO_TILE_INDEX = 0
GO_REWARD = 200
JAIL_TILE_INDEX = 10
TAX_AMOUNT = 200
INCOME_TAX_TILE = 4
LUXURY_TAX_TILE = 38


# ============================================================================
# DICE & MOVEMENT
# ============================================================================

def roll_dice() -> Tuple[int, int]:
    """
    Roll two six-sided dice.
    
    Returns:
        Tuple[int, int]: Two random integers between 1 and 6 (inclusive).
    """
    return (random.randint(1, 6), random.randint(1, 6))


def move_player(player: Dict[str, Any], steps: int) -> Dict[str, Any]:
    """
    Move a player forward by a given number of steps.
    
    If the player crosses or lands on GO (position 0), award GO_REWARD (200).
    Handles board wrapping via modulo.
    
    Args:
        player: Player dict with position and money.
        steps: Number of steps to move.
        
    Returns:
        Dict: Updated player dict.
    """
    old_position = player["position"]
    new_position = (old_position + steps) % BOARD_SIZE
    
    # Check if player crossed GO (wrapped around)
    crossed_go = new_position < old_position or (old_position + steps >= BOARD_SIZE)
    
    player["position"] = new_position
    if crossed_go:
        player["money"] += GO_REWARD
    
    return player


# ============================================================================
# TURN MANAGEMENT
# ============================================================================

def get_current_player(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the current player based on current_turn index.
    
    Args:
        game_state: GameState dict.
        
    Returns:
        Dict: Current player dict.
        
    Raises:
        IndexError: If current_turn is invalid or no players exist.
    """
    return game_state["players"][game_state["current_turn"]]


def next_turn(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advance to the next active (non-bankrupt) player's turn.
    
    Skips bankrupt players safely. Wraps around to beginning if needed.
    
    Args:
        game_state: GameState dict.
        
    Returns:
        Dict: Updated game_state dict with current_turn advanced.
    """
    num_players = len(game_state["players"])
    current_idx = game_state["current_turn"]
    
    # Find next non-bankrupt player
    for i in range(1, num_players + 1):
        next_idx = (current_idx + i) % num_players
        if not game_state["players"][next_idx].get("is_bankrupt", False):
            game_state["current_turn"] = next_idx
            return game_state
    
    # All players bankrupt (should not happen in normal game)
    game_state["current_turn"] = (current_idx + 1) % num_players
    return game_state


# ============================================================================
# RENT & PAYMENT
# ============================================================================

def calculate_rent(property_obj: Dict[str, Any]) -> int:
    """
    Calculate the rent for a property based on houses and hotel.
    
    Uses rent_levels list: [base, 1H, 2H, 3H, 4H, hotel]
    
    Args:
        property_obj: Property dict with rent_levels, houses, has_hotel.
        
    Returns:
        int: Rent amount to charge.
    """
    rent_levels = property_obj["rent_levels"]
    
    if property_obj["has_hotel"]:
        return rent_levels[5]  # Hotel is last index
    
    houses = property_obj["houses"]
    if houses > 0:
        return rent_levels[houses]  # 1-4 houses map to indices 1-4
    
    return rent_levels[0]  # Base rent (no improvements)


def pay_rent(
    paying_player: Dict[str, Any],
    receiving_player: Dict[str, Any],
    amount: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Transfer rent from one player to another.
    
    If paying_player runs out of money, mark as bankrupt.
    
    Args:
        paying_player: Player dict (payer).
        receiving_player: Player dict (receiver).
        amount: Rent amount to transfer.
        
    Returns:
        Tuple: (updated_paying_player, updated_receiving_player)
    """
    paying_player["money"] -= amount
    receiving_player["money"] += amount
    
    if paying_player["money"] < 0:
        paying_player["is_bankrupt"] = True
    
    return paying_player, receiving_player


# ============================================================================
# TILE ACTIONS
# ============================================================================

def handle_tile_action(
    player_idx: int,
    tile: Dict[str, Any],
    game_state: Dict[str, Any],
    properties_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute the action for the tile the player landed on.
    
    Handles different tile types:
    - PROPERTY/RAILROAD/UTILITY: Check ownership and calculate rent.
    - TAX: Deduct tax amount.
    - JAIL: Update position to jail.
    - CHANCE/COMMUNITY_CHEST: Placeholder (no logic yet).
    - GO/FREE_PARKING/CORNER: No action.
    - GO_TO_JAIL: Move to jail.
    
    Args:
        player_idx: Index of player in game_state.players.
        tile: Tile dict with type and property_id.
        game_state: GameState dict.
        properties_map: Dict mapping property_id to Property dict.
        
    Returns:
        Dict: Updated game_state.
    """
    tile_type = tile["type"]
    player = game_state["players"][player_idx]
    
    # -------- PROPERTY TILE --------
    if tile_type == TileType.PROPERTY:
        property_id = tile["property_id"]
        if not property_id or property_id not in properties_map:
            return game_state
        
        prop = properties_map[property_id]
        
        # If unowned, mark can_buy action (no purchase logic here)
        if not prop["owner_id"]:
            # Store action indicator (Phase 4 will handle actual purchase)
            player["action"] = {
                "type": "can_buy",
                "property_id": property_id,
                "price": prop["price"]
            }
            return game_state
        
        # If owned by another player, pay rent
        if prop["owner_id"] != player["id"]:
            owner_idx = _find_player_by_id(prop["owner_id"], game_state["players"])
            if owner_idx is not None:
                owner = game_state["players"][owner_idx]
                rent = calculate_rent(prop)
                player, owner = pay_rent(player, owner, rent)
                game_state["players"][player_idx] = player
                game_state["players"][owner_idx] = owner
        
        return game_state
    
    # -------- TAX TILE --------
    if tile_type == TileType.TAX:
        tax_amount = TAX_AMOUNT
        player["money"] -= tax_amount
        if player["money"] < 0:
            player["is_bankrupt"] = True
        game_state["players"][player_idx] = player
        return game_state
    
    # -------- JAIL TILE --------
    if tile_type == TileType.JAIL:
        player["position"] = JAIL_TILE_INDEX
        game_state["players"][player_idx] = player
        return game_state
    
    # -------- GO_TO_JAIL TILE --------
    if tile_type == TileType.GO_TO_JAIL:
        player["position"] = JAIL_TILE_INDEX
        game_state["players"][player_idx] = player
        return game_state
    
    # -------- CHANCE / COMMUNITY_CHEST --------
    if tile_type in [TileType.CHANCE, TileType.COMMUNITY_CHEST]:
        # Placeholder - no logic yet (Phase 5+)
        return game_state
    
    # -------- GO, FREE_PARKING, CORNER --------
    # No action needed
    return game_state


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _find_player_by_id(player_id: str, players: List[Dict[str, Any]]) -> int:
    """
    Find player index by player ID.
    
    Args:
        player_id: Player ID to search for.
        players: List of player dicts.
        
    Returns:
        int: Player index, or None if not found.
    """
    for idx, p in enumerate(players):
        if p["id"] == player_id:
            return idx
    return None


def is_game_over(game_state: Dict[str, Any]) -> bool:
    """
    Check if game is over (only one non-bankrupt player).
    
    Args:
        game_state: GameState dict.
        
    Returns:
        bool: True if game is over.
    """
    active_players = sum(1 for p in game_state["players"] if not p.get("is_bankrupt", False))
    return active_players <= 1


def get_winner(game_state: Dict[str, Any]) -> str:
    """
    Get the last remaining non-bankrupt player (winner).
    
    Args:
        game_state: GameState dict.
        
    Returns:
        str: Winner player ID, or None if no winner yet.
    """
    for p in game_state["players"]:
        if not p.get("is_bankrupt", False):
            return p["id"]
    return None


def check_game_end(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if game should end and mark it as ended if so.
    
    Phase 9: Game End Detection
    
    Rules:
    - Game ends when only 1 non-bankrupt player remains
    - Set phase to "ended"
    - Set winner to the last remaining player
    - Set ended_at timestamp
    
    Args:
        game_state: GameState dict.
        
    Returns:
        Dict: Updated game_state (with phase/winner set if game ended).
    """
    from datetime import datetime
    
    # Check if game already ended
    if game_state.get("phase") == "ended":
        return game_state
    
    # Count active players
    active_players = sum(1 for p in game_state["players"] if not p.get("is_bankrupt", False))
    
    # If only one player left, game ends
    if active_players <= 1:
        winner_id = get_winner(game_state)
        game_state["phase"] = "ended"
        game_state["winner"] = winner_id
        game_state["ended_at"] = datetime.utcnow().isoformat()
    
    return game_state
