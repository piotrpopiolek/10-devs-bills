from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Integer, Text, DateTime, Boolean, Numeric, 
    ForeignKey, Index, CheckConstraint, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, expression

from src.db.main import Base

if TYPE_CHECKING:
    from src.bills.models import Bill
    from src.product_indexes.models import ProductIndex

class VerificationSource(str, enum.Enum):
    AUTO = "auto"
    USER = "user"
    ADMIN = "admin"

class BillItem(Base):
    """
    BillItem model representing a single line item on a receipt.
    """
    __tablename__ = 'bill_items'
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative'),
        Index('idx_bill_items_bill_id', 'bill_id'),
        Index('idx_bill_items_index_id', 'index_id'),
        Index(
            'idx_bill_items_unverified', 
            'is_verified', 
            postgresql_where=(expression.column('is_verified') == False)
        ),
        {'comment': 'Individual bill items with verification and confidence tracking'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.false(), comment='Manual verification status for quality control')
    verification_source: Mapped[VerificationSource] = mapped_column(SAEnum(VerificationSource, name='verification_source', create_type=True),nullable=False,server_default=VerificationSource.AUTO.value)
    original_text: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), comment='OCR confidence score (0.00-1.00)')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    bill_id: Mapped[int] = mapped_column(Integer, ForeignKey('bills.id', ondelete='CASCADE'), nullable=False)
    index_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('product_indexes.id', ondelete='SET NULL'), nullable=True)
    bill: Mapped['Bill'] = relationship('Bill', back_populates='bill_items')
    index: Mapped[Optional['ProductIndex']] = relationship('ProductIndex', back_populates='bill_items')