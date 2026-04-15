"""
Game state model - Core game state management.
Represents the complete state of a game session.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum


class GamePhase(str, Enum):
    """Game phase enumeration - Represents the current phase of gameplay."""
    
    WAITING = "waiting"
    ROLLING = "rolling"
    MOVING = "moving"
    ACTION = "action"
    NEXT_TURN = "next_turn"
    ENDED = "ended"


class GameState(BaseModel):
    """
    Core game state model.
    
    IMPORTANT: This is the single source of truth for any active game.
    All game modifications happen through this model.
    """
    
    model_config = ConfigDict(
        use_enum_values=True,
        extra="ignore",
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "room_id": "room_1",
                "players": [
                    {
                        "id": "player_1",
                        "name": "Alice",
                        "emoji": "🔴",
                        "position": 5,
                        "money": 1200,
                        "properties": ["prop_1"],
                        "is_bot": False,
                        "is_bankrupt": False
                    }
                ],
                "properties": [
                    {
                        "id": "prop_1",
                        "name": "Google",
                        "price": 200,
                        "rent_levels": [20, 60, 180, 500, 1100, 1300],
                        "color_group": "blue",
                        "owner_id": "player_1",
                        "houses": 0,
                        "has_hotel": False
                    }
                ],
                "current_turn": 0,
                "dice": [4, 5],
                "phase": "action",
                "winner": None
            }
        }
    )
    
    room_id: str = Field(..., description="Unique room identifier")
    players: List[dict] = Field(..., description="List of Player objects in the game")
    properties: List[dict] = Field(..., description="List of all Property objects on board")
    current_turn: int = Field(default=0, ge=0, description="Index of current player's turn")
    dice: List[int] = Field(default_factory=lambda: [0, 0], description="Last dice roll result [die1, die2]")
    phase: GamePhase = Field(default=GamePhase.WAITING, description="Current game phase")
    winner: Optional[str] = Field(None, description="Player ID of winner, None if game not ended")
