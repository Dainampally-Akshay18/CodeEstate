"""
Tile model - Represents a single tile/square on the board.
"""

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional


class TileType(str, Enum):
    """Enumeration of all tile types on the board."""
    
    GO = "go"
    PROPERTY = "property"
    RAILROAD = "railroad"
    UTILITY = "utility"
    TAX = "tax"
    CHANCE = "chance"
    COMMUNITY_CHEST = "community_chest"
    JAIL = "jail"
    FREE_PARKING = "free_parking"
    GO_TO_JAIL = "go_to_jail"
    CORNER = "corner"


class Tile(BaseModel):
    """
    Tile data model.
    
    Represents a single tile/square on the game board.
    """
    
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 0,
                    "type": "go",
                    "property_id": None
                },
                {
                    "id": 1,
                    "type": "property",
                    "property_id": "prop_1"
                },
                {
                    "id": 10,
                    "type": "jail",
                    "property_id": None
                }
            ]
        }
    )
    
    id: int = Field(..., ge=0, le=39, description="Tile position on board (0-39)")
    type: TileType = Field(..., description="Type of tile (e.g., property, tax, jail)")
    property_id: Optional[str] = Field(
        None, 
        description="Property ID if this tile is a property, otherwise None"
    )
