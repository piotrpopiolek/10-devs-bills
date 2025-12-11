from decimal import Decimal
from typing import Optional
from pydantic import Field
from src.common.schemas import AppBaseModel

class NormalizedItem(AppBaseModel):
    """
    Normalized item after AI/Categorization process.
    Ready to be mapped to BillItem.
    """
    original_text: str = Field(..., description="Original OCR text")
    normalized_name: Optional[str] = Field(None, description="Normalized product name")
    
    quantity: Decimal = Field(default=Decimal("1.0"), description="Quantity")
    unit_price: Decimal = Field(..., description="Unit price")
    total_price: Decimal = Field(..., description="Total price")
    
    category_id: Optional[int] = Field(None, description="Category ID")
    product_index_id: Optional[int] = Field(None, description="Product Index ID")
    
    confidence_score: float = Field(default=1.0, description="Confidence score")
    
    is_confident: bool = Field(default=True, description="Is system confident about the result")

