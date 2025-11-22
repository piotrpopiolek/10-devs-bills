from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Integer, String, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.main import Base

if TYPE_CHECKING:
    from src.bills.models import Bill
    from src.product_index_aliases.models import ProductIndexAlias 

class Shop(Base):
    """
    Shop model representing a retail location.
    """
    __tablename__ = 'shops'
    
    __table_args__ = (
        Index('idx_shops_name', 'name'),
        UniqueConstraint('name', 'address', name='uq_shops_name_address'),
        {'comment': 'Shop information with unique name+address constraints'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    bills: Mapped[List['Bill']] = relationship('Bill', back_populates='shop')
    product_index_aliases: Mapped[List['ProductIndexAlias']] = relationship('ProductIndexAlias', back_populates='shop')