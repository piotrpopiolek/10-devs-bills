from typing import Sequence, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.common.services import AppService
from src.categories.models import Category
from src.categories.schemas import CategoryCreate, CategoryUpdate
from src.common.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError
from src.categories.exceptions import (
    CategoryCycleError,
    CategoryHasChildrenError
)

class CategoryService(AppService):
 
    async def get_by_id(self, category_id: int) -> Category:
        stmt = select(Category).where(Category.id == category_id)
        result = await self.session.execute(stmt)
        category = result.scalars().first()

        if not category:
            raise ResourceNotFoundError("Category", category_id)
        
        return category

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        stmt = select(Category).offset(skip).limit(limit).order_by(Category.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: CategoryCreate) -> Category:
        await self._ensure_unique(model=Category, field=Category.name, value=data.name, resource_name="Category", field_name="name")

        # Parent Existence Check (Referential Integrity check before DB hit)
        if data.parent_id:
            await self._ensure_exists(model=Category, field=Category.id, value=data.parent_id, resource_name="Parent Category")

        # Object Construction
        new_category = Category(
            name=data.name,
            parent_id=data.parent_id
        )

        # Persistence (Unit of Work)
        self.session.add(new_category)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_category)
        except IntegrityError as e:
            await self.session.rollback()
            raise ResourceAlreadyExistsError("Category", "name", data.name) from e

        return new_category

    async def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = await self.get_by_id(category_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return category

        if "name" in update_data and update_data["name"] != category.name:
            await self._ensure_unique(model=Category, field=Category.name, value=update_data["name"], resource_name="Category", field_name="name")

        if "parent_id" in update_data and update_data["parent_id"] != category.parent_id:
            if update_data["parent_id"] is not None:
                await self._ensure_exists(model=Category, field=Category.id, value=update_data["parent_id"], resource_name="Parent Category")
                
                # Logical check: Prevent circular dependency (basic self-reference check)
                if update_data["parent_id"] == category.id:
                    raise CategoryCycleError()

        # Apply updates
        for key, value in update_data.items():
            setattr(category, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(category)
        except IntegrityError:
            await self.session.rollback()
            raise ResourceAlreadyExistsError("Category", "name", data.name)

        return category

    async def delete(self, category_id: int) -> None:

        category = await self.get_by_id(category_id)
        
        await self.session.delete(category)
        
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise CategoryHasChildrenError()
