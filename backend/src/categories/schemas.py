from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class CategoriesQueryParams(BaseModel):
    """
    Query parameters for GET /categories endpoint.
    
    Attributes:
        parent_id: Optional parent category ID for filtering (must be > 0)
        include_children: Whether to include subcategories in response
    """
    parent_id: Optional[int] = Field(
        None,
        gt=0,
        description="Filter by parent category ID"
    )
    include_children: Optional[bool] = Field(
        False,
        description="Include subcategories in response"
    )

    @field_validator('parent_id')
    @classmethod
    def validate_parent_id(cls, v: Optional[int]) -> Optional[int]:
        """
        Validate that parent_id is a positive integer if provided.
        
        Args:
            v: The parent_id value to validate
            
        Returns:
            The validated parent_id value
            
        Raises:
            ValueError: If parent_id is not None and <= 0
        """
        if v is not None and v <= 0:
            raise ValueError('parent_id must be a positive integer')
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "parent_id": 1,
                "include_children": True
            }
        }


class CategoryResponse(BaseModel):
    """
    Response model for a single category with hierarchical structure.
    
    Attributes:
        id: Category ID
        name: Category name
        parent_id: Parent category ID (null for root categories)
        children: List of subcategories (recursive structure)
        products_count: Number of products in this category
        created_at: Creation timestamp
    """
    id: int
    name: str
    parent_id: Optional[int]
    children: List['CategoryResponse'] = Field(
        default_factory=list,
        description="List of subcategories"
    )
    products_count: int = Field(
        ge=0,
        description="Number of products in this category"
    )
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Food & Beverages",
                "parent_id": None,
                "children": [],
                "products_count": 150,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


# Forward reference resolution for recursive model
CategoryResponse.model_rebuild()


class CategoryListResponse(BaseModel):
    """
    Response model for list of categories.
    
    Attributes:
        categories: List of category responses
    """
    categories: List[CategoryResponse] = Field(
        default_factory=list,
        description="List of categories"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "categories": [
                    {
                        "id": 1,
                        "name": "Food & Beverages",
                        "parent_id": None,
                        "children": [],
                        "products_count": 150,
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }

