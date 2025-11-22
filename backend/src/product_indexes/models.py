from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from sqlalchemy import ForeignKey, Integer, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, GIN
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.main import Base

if TYPE_CHECKING:
    from src.categories.models import Category


class ProductIndex(Base):
    """
    Product index model representing a normalized product dictionary.
    
    Attributes:
        id: Primary key (auto-incremented)  
        name: Product name (unique, indexed) (not nullable)     
        synonyms: JSONB dictionary of synonyms (nullable)
        created_at: Timestamp of creation (not nullable, server default now())
        updated_at: Timestamp of last update (not nullable, server default now(), onupdate=now())
        category_id: Foreign key to category (nullable, indexed)
        category: Reference to category (self-referential)
        bill_items: List of bill items (back-populates 'index')
        product_index_aliases: List of product index aliases (back-populates 'index')
    """
    __tablename__ = 'product_indexes'
    __table_args__ = (
        # Indeks GIN dla JSONB - kluczowe dla wydajności wyszukiwania w JSON
        Index('idx_product_indexes_synonyms', 'synonyms', postgresql_using='gin'),
        Index('idx_product_indexes_category_id', 'category_id'),
        Index('idx_product_indexes_name', 'name'),
        {'comment': 'Normalized product dictionary with synonyms and category associations'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    synonyms: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('categories.id', ondelete='RESTRICT'), nullable=True)
    category: Mapped[Optional['Category']] = relationship('Category', back_populates='product_indexes')
    # bill_items: Mapped[List['BillItem']] = relationship('BillItem', back_populates='index')
    # aliases: Mapped[List['ProductIndexAlias']] = relationship('ProductIndexAlias', back_populates='index')
