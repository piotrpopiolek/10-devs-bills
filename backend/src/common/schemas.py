from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

class AppBaseModel(BaseModel):
    """
    Global base model for the application.
    Centralizes Pydantic configuration (strict mode, stripping, etc.).
    """
    model_config = ConfigDict(
        strict=True,                # No implicit type coercion (ex: "1" != 1)
        str_strip_whitespace=True,  # Auto-strip whitespace from strings
        validate_assignment=True,   # Validate values even when setting attributes after creation
        from_attributes=True,       # Enable ORM mode (SQLAlchemy -> Pydantic)
        frozen=False                # Allow mutation (default)
    )

class PaginatedResponse(AppBaseModel, Generic[T]):
    """
    Generic wrapper for paginated responses.
    
    Usage:
        class ShopListResponse(PaginatedResponse[ShopResponse]): pass
    """
    items: list[T] = Field(
        ...,
        description="List of items for the current page"
    )
    
    total: int = Field(
        ...,
        ge=0,
        description="Total number of items matching the query"
    )
    
    page: int = Field(
        ...,
        ge=1,
        description="Current page number"
    )
    
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page"
    )