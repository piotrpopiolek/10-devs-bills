from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Integer, String, Text, DateTime, 
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

from src.db.main import Base

if TYPE_CHECKING:
    from src.product_indexes.models import ProductIndex
    from src.shops.models import Shop
    from src.users.models import User

class ProductIndexAlias(Base):
    """
    ProductIndexAlias model.
    Maps raw OCR text (e.g., "Mleko 3.2%") to a normalized ProductIndex.
    Acts as the system's learning memory.
    """
    __tablename__ = 'product_index_aliases'
    
    __table_args__ = (
        Index('idx_product_index_aliases_raw_name', 'raw_name'),
        Index('idx_product_index_aliases_index_id', 'index_id'),
        Index('idx_product_index_aliases_shop_id', 'shop_id'),
        Index('idx_product_index_aliases_user_id', 'user_id'),
        UniqueConstraint('raw_name', 'index_id', name='uq_alias_raw_name_index'),
        {'comment': 'OCR text variants linked to normalized products with confirmation tracking'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_name: Mapped[str] = mapped_column(Text, nullable=False)
    confirmations_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'), comment='Number of times this alias was confirmed as correct')
    shop_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('shops.id', ondelete='SET NULL'), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    index_id: Mapped[int] = mapped_column(Integer, ForeignKey('product_indexes.id', ondelete='CASCADE'), nullable=False)
    locale: Mapped[Optional[str]] = mapped_column(String(10), default='pl_PL')
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    index: Mapped['ProductIndex'] = relationship('ProductIndex', back_populates='product_index_aliases')
    shop: Mapped[Optional['Shop']] = relationship('Shop', back_populates='product_index_aliases')
    user: Mapped[Optional['User']] = relationship('User', back_populates='product_index_aliases')