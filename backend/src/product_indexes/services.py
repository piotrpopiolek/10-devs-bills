from typing import Sequence, Optional
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from src.common.services import AppService
from src.product_indexes.models import ProductIndex
from src.product_indexes.schemas import ProductIndexCreate, ProductIndexUpdate
from src.common.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError
from src.categories.models import Category


class ProductIndexService(AppService):

    async def get_by_id(self, product_index_id: int) -> ProductIndex:
        stmt = select(ProductIndex).where(ProductIndex.id == product_index_id)
        result = await self.session.execute(stmt)
        product_index = result.scalar_one_or_none()

        if not product_index:
            raise ResourceNotFoundError("ProductIndex", product_index_id)
        
        return product_index

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ProductIndex]:
        stmt = select(ProductIndex).offset(skip).limit(limit).order_by(ProductIndex.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _ensure_unique_name(self, name: str, exclude_id: Optional[int] = None) -> None:
        """
        Checks if a product name (case-insensitive) already exists.
        Used to prevent duplicate product names.
        """
        stmt = select(ProductIndex).where(
            func.lower(ProductIndex.name) == func.lower(name)
        )
        
        if exclude_id is not None:
            stmt = stmt.where(ProductIndex.id != exclude_id)
        
        result = await self.session.execute(stmt)
        if result.scalars().first():
            raise ResourceAlreadyExistsError("ProductIndex", "name", name)

    async def create(self, data: ProductIndexCreate) -> ProductIndex:
        # Category Existence Check (if provided)
        if data.category_id:
            await self._ensure_exists(model=Category, field=Category.id, value=data.category_id, resource_name="Category")

        # Uniqueness Check (case-insensitive name)
        await self._ensure_unique_name(data.name)

        # Object Construction
        new_product_index = ProductIndex(
            name=data.name,
            synonyms=data.synonyms,
            category_id=data.category_id
        )

        # Persistence (Unit of Work)
        self.session.add(new_product_index)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_product_index)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "uq_product_indexes_name_lower" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("ProductIndex", "name", data.name) from e
            raise e

        return new_product_index

    async def update(self, product_index_id: int, data: ProductIndexUpdate) -> ProductIndex:
        product_index = await self.get_by_id(product_index_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return product_index

        # Category Existence Check (if category_id is being updated)
        if "category_id" in update_data and update_data["category_id"] != product_index.category_id:
            new_category_id = update_data["category_id"]
            if new_category_id is not None:
                await self._ensure_exists(model=Category, field=Category.id, value=new_category_id, resource_name="Category")

        # Uniqueness Check (if name is being updated)
        if "name" in update_data and update_data["name"] != product_index.name:
            await self._ensure_unique_name(update_data["name"], exclude_id=product_index.id)

        # Apply updates
        for key, value in update_data.items():
            setattr(product_index, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(product_index)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "uq_product_indexes_name_lower" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("ProductIndex", "name", update_data.get("name", product_index.name)) from e
            raise e

        return product_index

    async def delete(self, product_index_id: int) -> None:
        product_index = await self.get_by_id(product_index_id)
        
        self.session.delete(product_index)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e

