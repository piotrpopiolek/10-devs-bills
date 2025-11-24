from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from src.common.schemas import AppBaseModel, PaginatedResponse

class UserValidationMixin:
    
    @field_validator('external_id', check_fields=False)
    @classmethod
    def validate_external_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("External ID must be a positive integer")
        return v

    @field_validator('is_active', check_fields=False)
    @classmethod
    def validate_is_active(cls, v: Optional[bool]) -> Optional[bool]:
        # Boolean validation is handled by Pydantic, but we can add custom logic if needed
        return v

# --- BASE MODEL ---
class UserBase(AppBaseModel, UserValidationMixin):
    
    external_id: int = Field(
        ...,
        gt=0,
        description="Telegram user ID for external authentication (required, must be positive)"
    )
    
    is_active: bool = Field(
        True,
        description="User activity status (default: true)"
    )

class UserCreate(UserBase):
    pass

class UserUpdate(AppBaseModel, UserValidationMixin):
    
    external_id: Optional[int] = Field(
        None,
        gt=0,
        description="Telegram user ID (typically should not be changed)"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="User activity status"
    )

# --- RESPONSES ---
class UserResponse(UserBase):
    id: int = Field(..., gt=0)
    created_at: datetime
    updated_at: datetime

class ShopListResponse(PaginatedResponse[UserResponse]):
    pass

