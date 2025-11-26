from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator
from src.common.schemas import AppBaseModel, PaginatedResponse

class ProductIndexAliasValidationMixin:
    
    @field_validator('raw_name', check_fields=False)
    @classmethod
    def validate_raw_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Raw name cannot be empty or whitespace only")
        return v

    @field_validator('confirmations_count', check_fields=False)
    @classmethod
    def validate_confirmations_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 0:
                raise ValueError("Confirmations count cannot be negative")
        return v

    @field_validator('shop_id', check_fields=False)
    @classmethod
    def validate_shop_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("Shop ID must be a positive integer")
        return v

    @field_validator('user_id', check_fields=False)
    @classmethod
    def validate_user_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("User ID must be a positive integer")
        return v

    @field_validator('index_id', check_fields=False)
    @classmethod
    def validate_index_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("Index ID must be a positive integer")
        return v

    @field_validator('locale', check_fields=False)
    @classmethod
    def validate_locale(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) > 10:
                raise ValueError("Locale cannot exceed 10 characters")
        return v or None

# --- BASE MODEL ---
class ProductIndexAliasBase(AppBaseModel, ProductIndexAliasValidationMixin):

    raw_name: str = Field(
        ...,
        min_length=1,
        description="Raw OCR text (required, cannot be empty)"
    )
    
    confirmations_count: int = Field(
        0,
        ge=0,
        description="Number of times this alias was confirmed as correct (default: 0)"
    )
    
    shop_id: Optional[int] = Field(
        None,
        gt=0,
        description="Shop ID (optional, must be positive)"
    )
    
    user_id: Optional[int] = Field(
        None,
        gt=0,
        description="User ID (optional, must be positive)"
    )
    
    index_id: int = Field(
        ...,
        gt=0,
        description="Product index ID (required, must be positive)"
    )
    
    locale: Optional[str] = Field(
        'pl_PL',
        max_length=10,
        description="Locale of the alias (optional, default: pl_PL, max 10 characters)"
    )

class ProductIndexAliasCreate(ProductIndexAliasBase):
    pass

class ProductIndexAliasUpdate(AppBaseModel, ProductIndexAliasValidationMixin):
    
    raw_name: Optional[str] = Field(
        None,
        min_length=1,
        description="Raw OCR text"
    )
    
    confirmations_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of times this alias was confirmed as correct"
    )
    
    shop_id: Optional[int] = Field(
        None,
        gt=0,
        description="Shop ID"
    )
    
    user_id: Optional[int] = Field(
        None,
        gt=0,
        description="User ID"
    )
    
    index_id: Optional[int] = Field(
        None,
        gt=0,
        description="Product index ID"
    )
    
    locale: Optional[str] = Field(
        None,
        max_length=10,
        description="Locale of the alias"
    )

# --- RESPONSES ---
class ProductIndexAliasResponse(ProductIndexAliasBase):
    id: int = Field(..., gt=0)
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class ProductIndexAliasListResponse(PaginatedResponse[ProductIndexAliasResponse]):
    pass

