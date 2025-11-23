from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

class AppBaseModel(BaseModel):
    model_config = ConfigDict(
        strict=True,                # No implicit type coercion (ex: "1" != 1)
        str_strip_whitespace=True,  # Auto-strip whitespace from strings (built-in Pydantic feature!)
        validate_assignment=True,   # Validate values even when setting attributes after creation
        from_attributes=True,       # Enable ORM mode (SQLAlchemy -> Pydantic)
        frozen=False                # Allow mutation (default)
    )

class ShopValidationMixin:
    
    @field_validator('name', check_fields=False)
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v:
                 raise ValueError("Shop name cannot be empty")
        return v

    @field_validator('address', check_fields=False)
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        return v or None

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

    model_config = ConfigDict(
        strict=True,
        from_attributes=True,
        str_strip_whitespace=True
    )

class ShopListResponse(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)
    items: list[ShopResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)