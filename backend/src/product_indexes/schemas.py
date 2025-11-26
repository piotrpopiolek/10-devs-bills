from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from src.common.schemas import AppBaseModel, PaginatedResponse

class ProductIndexValidationMixin:
    
    @field_validator('name', check_fields=False)
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v:
                raise ValueError("Product name cannot be empty")
        return v

    @field_validator('category_id', check_fields=False)
    @classmethod
    def validate_category_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("Category ID must be a positive integer")
        return v

    @field_validator('synonyms', check_fields=False)
    @classmethod
    def validate_synonyms(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        # JSONB validation - Pydantic will handle dict structure validation
        # We can add custom validation here if needed (e.g., max depth, key constraints)
        return v or None

# --- BASE MODEL ---
class ProductIndexBase(AppBaseModel, ProductIndexValidationMixin):

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Product name (required, 1-255 characters, case-insensitive unique)"
    )
    
    synonyms: Optional[Dict[str, Any]] = Field(
        None,
        description="JSONB dictionary of product synonyms (optional)"
    )
    
    category_id: Optional[int] = Field(
        None,
        gt=0,
        description="Category ID (optional, must be positive)"
    )

class ProductIndexCreate(ProductIndexBase):
    pass

class ProductIndexUpdate(AppBaseModel, ProductIndexValidationMixin):
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Product name"
    )
    
    synonyms: Optional[Dict[str, Any]] = Field(
        None,
        description="JSONB dictionary of product synonyms"
    )
    
    category_id: Optional[int] = Field(
        None,
        gt=0,
        description="Category ID"
    )

# --- RESPONSES ---
class ProductIndexResponse(ProductIndexBase):
    id: int = Field(..., gt=0)
    created_at: datetime
    updated_at: datetime

class ProductIndexListResponse(PaginatedResponse[ProductIndexResponse]):
    pass

