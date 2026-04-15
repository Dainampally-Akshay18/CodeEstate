"""
Room model - Represents a game room/session.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


class RoomStatus(str, Enum):
    """Enumeration of room statuses."""
    
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class Room(BaseModel):
    """
    Room/Game session model.
    
    Represents a game room that contains players and tracks the game state.
    """
    
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "room_id": "room_1",
                "status": "playing",
                "players": ["player_1", "player_2"],
                "game_state": {
                    "room_id": "room_1",
                    "players": [],
                    "properties": [],
                    "current_turn": 0,
                    "dice": [0, 0],
                    "phase": "waiting",
                    "winner": None
                },
                "created_at": "2026-04-15T10:30:00",
                "expires_at": None
            }
        }
    )
    
    room_id: str = Field(..., description="Unique room identifier")
    status: RoomStatus = Field(default=RoomStatus.WAITING, description="Current room status")
    players: List[str] = Field(default_factory=list, description="List of player IDs in room")
    game_state: dict = Field(..., description="GameState object representing current game state")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Room creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Room expiration timestamp (for cleanup)")
