from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.common.services import AppService
from src.shops.models import Shop
from src.shops.schemas import ShopCreate, ShopUpdate
from src.common.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


class ShopService(AppService):

    async def get_by_id(self, shop_id: int) -> Shop:
        stmt = select(Shop).where(Shop.id == shop_id)
        result = await self.session.execute(stmt)
        shop = result.scalar_one_or_none()

        if not shop:
            raise ResourceNotFoundError("Shop", shop_id)
        
        return shop

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Shop]:
        stmt = select(Shop).offset(skip).limit(limit).order_by(Shop.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _ensure_unique_shop(self, name: str, address: Optional[str], exclude_id: Optional[int] = None) -> None:
        """
        Checks if a combination of name and address already exists.
        Used to prevent duplicate shops with the same name and address.
        Note: This is case-sensitive (not using LOWER) as per database constraint.
        """
        stmt = select(Shop).where(
            Shop.name == name,
            Shop.address == address
        )
        
        if exclude_id is not None:
            stmt = stmt.where(Shop.id != exclude_id)
        
        result = await self.session.execute(stmt)
        if result.scalars().first():
            raise ResourceAlreadyExistsError("Shop", "name + address", f"{name} + {address or 'NULL'}")

    async def create(self, data: ShopCreate) -> Shop:
        # Uniqueness Check (name + address combination)
        await self._ensure_unique_shop(data.name, data.address)

        # Object Construction
        new_shop = Shop(
            name=data.name,
            address=data.address
        )

        # Persistence (Unit of Work)
        self.session.add(new_shop)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_shop)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "uq_shops_name_address" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("Shop", "name + address", f"{data.name} + {data.address or 'NULL'}") from e
            raise e

        return new_shop

    async def update(self, shop_id: int, data: ShopUpdate) -> Shop:
        shop = await self.get_by_id(shop_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return shop

        # Uniqueness Check (if name or address is being updated)
        new_name = update_data.get("name", shop.name)
        new_address = update_data.get("address", shop.address)
        
        if "name" in update_data or "address" in update_data:
            if new_name != shop.name or new_address != shop.address:
                await self._ensure_unique_shop(new_name, new_address, exclude_id=shop.id)

        # Apply updates
        for key, value in update_data.items():
            setattr(shop, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(shop)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "uq_shops_name_address" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("Shop", "name + address", f"{new_name} + {new_address or 'NULL'}") from e
            raise e

        return shop

    async def delete(self, shop_id: int) -> None:
        shop = await self.get_by_id(shop_id)
        
        self.session.delete(shop)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e

