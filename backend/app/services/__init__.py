"""
Services module for business logic.
Contains game engine, property service, room service, and other core services.
"""

# Game Engine
from app.services.game_engine import (
    roll_dice,
    move_player,
    get_current_player,
    next_turn,
    calculate_rent,
    pay_rent,
    handle_tile_action,
    is_game_over,
    get_winner,
    check_game_end,
)

# Property Service
from app.services.property_service import (
    buy_property,
    process_rent,
    get_property_by_id,
    get_player_by_id,
    find_player_index,
    PropertyServiceError,
    InvalidPropertyError,
    PropertyOwnedError,
    InsufficientFundsError,
    InvalidTurnError,
)

# Room Service
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
    list_all_rooms,
    RoomServiceError,
    RoomNotFoundError,
    RoomFullError,
    GameAlreadyStartedError,
    InsufficientPlayersError,
    InvalidGameStateError,
)

# Bot Engine (Phase 8)
from app.services.bot_engine import (
    decide_action,
    execute_bot_turn,
    execute_bot_sequence,
)

__all__ = [
    # Game Engine
    "roll_dice",
    "move_player",
    "get_current_player",
    "next_turn",
    "calculate_rent",
    "pay_rent",
    "handle_tile_action",
    "is_game_over",
    "get_winner",
    "check_game_end",
    # Property Service
    "buy_property",
    "process_rent",
    "get_property_by_id",
    "get_player_by_id",
    "find_player_index",
    "PropertyServiceError",
    "InvalidPropertyError",
    "PropertyOwnedError",
    "InsufficientFundsError",
    "InvalidTurnError",
    # Room Service
    "create_room",
    "get_room",
    "get_game_state",
    "join_room",
    "start_game",
    "get_room_players",
    "get_player_count",
    "is_room_full",
    "is_game_started",
    "list_all_rooms",
    "RoomServiceError",
    "RoomNotFoundError",
    "RoomFullError",
    "GameAlreadyStartedError",
    "InsufficientPlayersError",
    "InvalidGameStateError",
    # Bot Engine (Phase 8)
    "decide_action",
    "execute_bot_turn",
    "execute_bot_sequence",
]
