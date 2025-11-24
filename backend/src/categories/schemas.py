from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator
from src.common.schemas import AppBaseModel, PaginatedResponse

class CategoryValidationMixin:
    
    @field_validator('name', check_fields=False)
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v:
                raise ValueError("Category name cannot be empty")
        return v

    @field_validator('parent_id', check_fields=False)
    @classmethod
    def validate_parent_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("Parent ID must be a positive integer")
        return v

# --- BASE MODEL ---
class CategoryBase(AppBaseModel, CategoryValidationMixin):

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Category name (required, 1-255 characters, unique)"
    )
    
    parent_id: Optional[int] = Field(
        None,
        gt=0,
        description="Parent category ID (optional, must be positive, null for root categories)"
    )

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(AppBaseModel, CategoryValidationMixin):
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Category name"
    )
    
    parent_id: Optional[int] = Field(
        None,
        gt=0,
        description="Parent category ID"
    )

# --- RESPONSES ---
class CategoryResponse(CategoryBase):
    id: int = Field(..., gt=0)
    created_at: datetime
    updated_at: datetime

class CategoryListResponse(PaginatedResponse[CategoryResponse]):
    pass
