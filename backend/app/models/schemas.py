"""
Tech Monopoly - Core Application Models
Game state structures for Phase 2+
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PlayerModel(BaseModel):
    """Player data model (will be expanded in Phase 2)."""
    
    id: str = Field(..., description="Unique player ID")
    emoji: str = Field(..., description="Player emoji representation")
    position: int = Field(default=0, description="Current board position (0-39)")
    money: int = Field(default=1500, description="Player wallet balance")
    properties: List[str] = Field(default_factory=list, description="Owned property IDs")
    is_bot: bool = Field(default=False, description="Is player a bot")


class PropertyModel(BaseModel):
    """Property data model (will be expanded in Phase 4)."""
    
    id: str = Field(..., description="Property ID")
    name: str = Field(..., description="Tech brand name")
    color: str = Field(..., description="Color group")
    price: int = Field(..., description="Purchase price")
    owner: Optional[str] = Field(None, description="Owner player ID")


class RoomModel(BaseModel):
    """Room/game session model."""
    
    room_id: str = Field(..., description="Unique room identifier")
    status: str = Field(default="waiting", description="Room status")
    players: List[str] = Field(default_factory=list, description="Player IDs in room")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Room expiration time")
