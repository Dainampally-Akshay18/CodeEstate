"""
Models module for data structures.
Contains Pydantic models for request/response handling and game logic.
"""

from pydantic import BaseModel

# Response Models
class BaseResponseModel(BaseModel):
    """Base response model for all API responses."""

    success: bool
    message: str


class ErrorResponseModel(BaseResponseModel):
    """Error response model."""

    error: str


# Domain Models
from app.models.player import Player
from app.models.property import Property
from app.models.tile import Tile, TileType
from app.models.game_state import GameState, GamePhase
from app.models.room import Room, RoomStatus

__all__ = [
    # Response Models
    "BaseResponseModel",
    "ErrorResponseModel",
    # Domain Models
    "Player",
    "Property",
    "Tile",
    "TileType",
    "GameState",
    "GamePhase",
    "Room",
    "RoomStatus",
]
