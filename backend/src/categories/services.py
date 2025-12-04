from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.services import AppService
from src.categories.models import Category
from src.categories.schemas import CategoryCreate, CategoryUpdate
from src.common.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError
from src.categories.exceptions import (
    CategoryCycleError,
    CategoryHasChildrenError
)

class CategoryService(AppService[Category, CategoryCreate, CategoryUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Category, session=session)

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
            new_parent_id = update_data["parent_id"]
            if new_parent_id is not None:
                # Sprawdzenie istnienia rodzica
                await self._ensure_exists(model=Category, field=Category.id, value=new_parent_id, resource_name="Parent Category")
                
                # Zabezpieczenie przed cyklami (sprawdzenie czy nowy rodzic nie jest potomkiem edytowanej kategorii)
                if await self._check_is_descendant(ancestor_id=category.id, descendant_id=new_parent_id):
                    raise CategoryCycleError()

        # Apply updates
        for key, value in update_data.items():
            setattr(category, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(category)
        except IntegrityError as e:
            await self.session.rollback()
            raise ResourceAlreadyExistsError("Category", "name", data.name) from e

        return category

    async def delete(self, category_id: int) -> None:

        category = await self.get_by_id(category_id)
        
        self.session.delete(category)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            
            if self._is_foreign_key_violation(e):
                raise CategoryHasChildrenError() from e
                
            raise e

    async def _check_is_descendant(self, ancestor_id: int, descendant_id: int) -> bool:
        """
        Checks if descendant_id is actually a descendant of ancestor_id (or the same).
        Used to prevent cycles when moving a category.
        """
        if ancestor_id == descendant_id:
            return True

        # Recursive CTE to walk up the tree (from descendant to root)
        cte = select(Category.id, Category.parent_id).where(Category.id == descendant_id).cte(name="ancestry", recursive=True)
        
        parent_alias = select(Category.id, Category.parent_id).join(cte, Category.id == cte.c.parent_id)
        cte = cte.union_all(parent_alias)
        
        stmt = select(cte.c.id).where(cte.c.id == ancestor_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
