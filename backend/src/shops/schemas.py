from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator
from src.common.schemas import AppBaseModel, PaginatedResponse
from src.shops.normalization import normalize_shop_name, normalize_shop_address

class ShopValidationMixin:
    
    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalizuje nazwę sklepu przed walidacją.
        
        Transformacje: lowercase, trim, usunięcie cudzysłowów, normalizacja białych znaków.
        """
        if v is not None:
            normalized = normalize_shop_name(v)
            if not normalized:
                raise ValueError("Shop name cannot be empty after normalization")
            return normalized
        return v

    @field_validator('address', mode='before')
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalizuje adres sklepu przed walidacją.
        
        Transformacje: lowercase, trim, usunięcie przecinków, normalizacja skrótu ul., 
        usunięcie średników (wielokrotne adresy), normalizacja białych znaków.
        """
        if v is not None:
            return normalize_shop_address(v)
        return None

# --- BASE MODEL ---
class ShopBase(AppBaseModel, ShopValidationMixin):

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the shop (required, 1-255 characters)"
    )
    
    address: Optional[str] = Field(
        None,
        max_length=255,
        description="Address of the shop (optional, max 255 characters)"
    )

class ShopCreate(ShopBase):
    pass

class ShopUpdate(AppBaseModel, ShopValidationMixin):
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Name of the shop"
    )
    
    address: Optional[str] = Field(
        None,
        max_length=255,
        description="Address of the shop"
    )

# --- RESPONSES ---
class ShopResponse(ShopBase):
    id: int = Field(..., gt=0)
    created_at: datetime
    updated_at: datetime

class ShopListResponse(PaginatedResponse[ShopResponse]):
    pass