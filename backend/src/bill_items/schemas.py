from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field, field_validator
from src.common.schemas import AppBaseModel, PaginatedResponse
from src.bill_items.models import VerificationSource

class BillItemValidationMixin:
    
    @field_validator('quantity', check_fields=False)
    @classmethod
    def validate_quantity(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v <= 0:
                raise ValueError("Quantity must be positive")
        return v

    @field_validator('confidence_score', check_fields=False)
    @classmethod
    def validate_confidence_score(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < 0 or v > 1:
                raise ValueError("Confidence score must be between 0.00 and 1.00")
        return v

    @field_validator('bill_id', check_fields=False)
    @classmethod
    def validate_bill_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("Bill ID must be a positive integer")
        return v

    @field_validator('index_id', check_fields=False)
    @classmethod
    def validate_index_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v <= 0:
                raise ValueError("Index ID must be a positive integer")
        return v

    @field_validator('original_text', check_fields=False)
    @classmethod
    def validate_original_text(cls, v: Optional[str]) -> Optional[str]:
        return v or None

# --- BASE MODEL ---
class BillItemBase(AppBaseModel, BillItemValidationMixin):

    quantity: Decimal = Field(
        ...,
        gt=0,
        description="Quantity of the item (required, must be positive, max 10 digits with 4 decimal places)"
    )
    
    unit_price: Decimal = Field(
        ...,
        description="Unit price of the item (required, must be non-negative, max 12 digits with 2 decimal places)"
    )
    
    total_price: Decimal = Field(
        ...,
        description="Total price of the item (required, must be non-negative, max 12 digits with 2 decimal places)"
    )
    
    is_verified: bool = Field(
        False,
        description="Manual verification status (default: false)"
    )
    
    verification_source: VerificationSource = Field(
        VerificationSource.AUTO,
        description="Source of verification (default: auto)"
    )
    
    bill_id: int = Field(
        ...,
        gt=0,
        description="Bill ID (required, must be positive)"
    )
    
    index_id: Optional[int] = Field(
        None,
        gt=0,
        description="Product index ID (optional, must be positive)"
    )
    
    original_text: Optional[str] = Field(
        None,
        description="Original OCR text of the item (optional)"
    )
    
    confidence_score: Optional[Decimal] = Field(
        None,
        ge=0,
        le=1,
        description="OCR confidence score (optional, range 0.00-1.00, max 3 digits with 2 decimal places)"
    )
    
    category_id: Optional[int] = Field(
        None,
        gt=0,
        description="Category ID (optional, must be positive)"
    )

class BillItemCreate(BillItemBase):
    pass

class BillItemUpdate(AppBaseModel, BillItemValidationMixin):
    
    quantity: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Quantity of the item"
    )
    
    unit_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Unit price of the item"
    )
    
    total_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Total price of the item"
    )
    
    is_verified: Optional[bool] = Field(
        None,
        description="Manual verification status"
    )
    
    verification_source: Optional[VerificationSource] = Field(
        None,
        description="Source of verification"
    )
    
    bill_id: Optional[int] = Field(
        None,
        gt=0,
        description="Bill ID"
    )
    
    index_id: Optional[int] = Field(
        None,
        gt=0,
        description="Product index ID"
    )
    
    original_text: Optional[str] = Field(
        None,
        description="Original OCR text of the item"
    )
    
    confidence_score: Optional[Decimal] = Field(
        None,
        ge=0,
        le=1,
        description="OCR confidence score"
    )

# --- RESPONSES ---
class BillItemResponse(BillItemBase):
    id: int = Field(..., gt=0)
    created_at: datetime
    index_name: Optional[str] = Field(
        None,
        description="Name of the product index associated with this bill item (loaded from index relationship)"
    )
    category_name: Optional[str] = Field(
        None,
        description="Name of the category associated with this bill item (loaded from category relationship)"
    )

class BillItemListResponse(PaginatedResponse[BillItemResponse]):
    pass
