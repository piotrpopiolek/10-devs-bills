from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


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
    model_config = ConfigDict(
        strict=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Food & Beverages",
                "parent_id": None,
                "children": [],
                "products_count": 150,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )
    
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


# Forward reference resolution for recursive model
CategoryResponse.model_rebuild()


class CategoryListResponse(BaseModel):
    """
    Response model for list of categories.
    
    Attributes:
        categories: List of category responses
    """
    model_config = ConfigDict(
        strict=True,
        json_schema_extra={
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
    )
    
    categories: List[CategoryResponse] = Field(
        default_factory=list,
        description="List of categories"
    )

