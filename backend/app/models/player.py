"""
Player model - Represents a player in the game.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List


class Player(BaseModel):
    """
    Player data model.
    
    Represents a single player in the game with all necessary attributes.
    """
    
    model_config = ConfigDict(extra="ignore", validate_assignment=True)
    
    id: str = Field(..., description="Unique player identifier")
    name: str = Field(..., description="Player's display name")
    emoji: str = Field(..., description="Player's emoji representation")
    position: int = Field(default=0, ge=0, le=39, description="Current board position (0-39)")
    money: int = Field(default=1500, ge=0, description="Player's current money/balance")
    properties: List[str] = Field(default_factory=list, description="List of property IDs owned by player")
    is_bot: bool = Field(default=False, description="Whether this player is AI-controlled")
    is_bankrupt: bool = Field(default=False, description="Whether player is bankrupt and out of game")
    
    class Config:
        """Pydantic config for serialization."""
        json_schema_extra = {
            "example": {
                "id": "player_1",
                "name": "Alice",
                "emoji": "🔴",
                "position": 5,
                "money": 1200,
                "properties": ["prop_1", "prop_3"],
                "is_bot": False,
                "is_bankrupt": False
            }
        }
