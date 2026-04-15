"""
Schemas module - DEPRECATED

This module is deprecated. Import models directly from their respective modules:
- from app.models.player import Player
- from app.models.property import Property
- from app.models.tile import Tile, TileType
- from app.models.game_state import GameState, GamePhase
- from app.models.room import Room, RoomStatus

Or import from app.models directly:
- from app.models import Player, Property, Tile, GameState, Room

This file is kept for backwards compatibility only.
"""

# Re-export models for backwards compatibility
from app.models.player import Player as PlayerModel
from app.models.property import Property as PropertyModel
from app.models.room import Room as RoomModel

__all__ = ["PlayerModel", "PropertyModel", "RoomModel"]
