"""
Property model - Represents a purchasable property on the board.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class Property(BaseModel):
    """
    Property data model.
    
    Represents a purchasable property on the game board with rent levels,
    owner info, and house/hotel status.
    """
    
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "id": "prop_1",
                "name": "Google",
                "price": 200,
                "rent_levels": [20, 60, 180, 500, 1100, 1300],
                "color_group": "blue",
                "owner_id": "player_1",
                "houses": 2,
                "has_hotel": False
            }
        }
    )
    
    id: str = Field(..., description="Unique property identifier")
    name: str = Field(..., description="Property/company name (e.g., 'Google', 'Tesla')")
    price: int = Field(..., ge=0, description="Purchase price of the property")
    rent_levels: List[int] = Field(
        ..., 
        description="Rent amounts for different states: [base, 1H, 2H, 3H, 4H, hotel]"
    )
    color_group: str = Field(..., description="Color group/category of property")
    owner_id: Optional[str] = Field(None, description="Player ID of current owner, None if unowned")
    houses: int = Field(default=0, ge=0, le=4, description="Number of houses on property (0-4)")
    has_hotel: bool = Field(default=False, description="Whether property has a hotel")
