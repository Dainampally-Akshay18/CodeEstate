"""
Game state models.
Core data structures for the game (initialized in Phase 2).
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class GamePhase(str, Enum):
    """Game phase enumeration."""

    WAITING = "waiting"
    ROLLING = "rolling"
    MOVING = "moving"
    ACTION = "action"
    NEXT_TURN = "next_turn"
    ENDED = "ended"


class GameState(BaseModel):
    """
    Core game state model.
    
    IMPORTANT: This is the single source of truth.
    All game modifications happen through this model.
    """

    room_id: str = Field(..., description="Unique room identifier")
    status: str = Field(default="waiting", description="Room status")
    phase: GamePhase = Field(default=GamePhase.WAITING, description="Current game phase")
    players: List[dict] = Field(default_factory=list, description="List of players in game")
    properties: List[dict] = Field(default_factory=list, description="All properties on board")
    current_turn: int = Field(default=0, description="Index of current player's turn")
    dice: tuple = Field(default=(0, 0), description="Last dice roll result")
    created_at: float = Field(..., description="Game creation timestamp")
    expires_at: Optional[float] = Field(None, description="Game expiration timestamp")

    class Config:
        """Pydantic config."""
        use_enum_values = True
