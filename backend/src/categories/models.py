from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import ForeignKey, Index, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.main import Base

if TYPE_CHECKING:
    from src.product_indexes.models import ProductIndex
    from src.bill_items.models import BillItem

class Category(Base):
    """
    Category model representing hierarchical product categories.
    
    Attributes:
        id: Primary key
        name: Category name (unique, indexed)
        parent_id: Foreign key to parent category (nullable for root categories, indexed)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        parent: Reference to parent category (self-referential)
        children: List of child categories
        product_indexes: List of products in this category
    """
    __tablename__ = "categories"
    __table_args__ = (
        Index('idx_categories_name', 'name'),
        Index('idx_categories_parent_id', 'parent_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True)     
    parent: Mapped[Optional['Category']] = relationship('Category', foreign_keys=[parent_id], remote_side=[id], back_populates='children')
    children: Mapped[list['Category']] = relationship('Category', foreign_keys=[parent_id], back_populates='parent')
    product_indexes: Mapped[list['ProductIndex']] = relationship('ProductIndex', back_populates='category')
    bill_items_categorized: Mapped[List['BillItem']] = relationship('BillItem', back_populates='category')
    




