from typing import Type, Any, TypeVar
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import ColumnElement

from src.common.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

class AppService:
    """
    Base service class that provides common functionality 
    like session management and generic validation checks.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _ensure_unique(
        self, 
        model: Type[ModelType], 
        field: ColumnElement, 
        value: Any, 
        resource_name: str,
        field_name: str
    ) -> None:
        """
        Generic check if a record with a given field value already exists.
        
        Args:
            model: The SQLAlchemy model class (e.g., Category)
            field: The SQLAlchemy column attribute (e.g., Category.name)
            value: The value to check
            resource_name: Name of the resource for the error message (e.g., "Category")
            field_name: Name of the field for the error message (e.g., "name")
        """
        stmt = select(model).where(field == value)
        result = await self.session.execute(stmt)
        if result.scalars().first():
            raise ResourceAlreadyExistsError(resource_name, field_name, value)

    async def _ensure_exists(
        self,
        model: Type[ModelType],
        field: ColumnElement,
        value: Any,
        resource_name: str
    ) -> None:
        """
        Generic check to ensure a related record exists (e.g. parent_id).
        """
        stmt = select(model).where(field == value)
        result = await self.session.execute(stmt)
        if not result.scalars().first():
            raise ResourceNotFoundError(resource_name, value)

    def _is_foreign_key_violation(self, e: IntegrityError) -> bool:
        """
        Checks if the IntegrityError is caused by a foreign key violation.
        Supports both asyncpg (sqlstate) and psycopg2 (pgcode).
        """
        # asyncpg puts sqlstate in e.orig.sqlstate
        if hasattr(e.orig, 'sqlstate') and e.orig.sqlstate == '23503':
            return True
        # psycopg2 puts pgcode in e.orig.pgcode
        if hasattr(e.orig, 'pgcode') and e.orig.pgcode == '23503':
            return True
        return False
