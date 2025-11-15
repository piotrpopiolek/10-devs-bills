from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.main import Base
from src.categories.models import Category

class Index(Base):
    """
    Index model representing normalized products in the dictionary.
    
    Attributes:
        id: Primary key
        name: Product name (unique)
        synonyms: JSONB field for product synonyms
        category_id: Foreign key to category
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "indexes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    synonyms = Column(JSON, nullable=True)  # JSONB in PostgreSQL
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    category = relationship(
        "Category",
        back_populates="indexes"
    )