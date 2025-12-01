from typing import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.common.services import AppService
from src.bills.models import Bill
from src.bills.schemas import BillCreate, BillUpdate
from src.common.exceptions import ResourceNotFoundError
from src.users.models import User
from src.shops.models import Shop


class BillService(AppService):

    async def get_by_id(self, bill_id: int) -> Bill:
        stmt = select(Bill).where(Bill.id == bill_id)
        result = await self.session.execute(stmt)
        bill = result.scalar_one_or_none()

        if not bill:
            raise ResourceNotFoundError("Bill", bill_id)
        
        return bill

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Bill]:
        stmt = select(Bill).offset(skip).limit(limit).order_by(Bill.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: BillCreate) -> Bill:
        # User Existence Check (Referential Integrity check before DB hit)
        await self._ensure_exists(model=User, field=User.id, value=data.user_id, resource_name="User")

        # Shop Existence Check (if provided)
        if data.shop_id:
            await self._ensure_exists(model=Shop, field=Shop.id, value=data.shop_id, resource_name="Shop")

        # Object Construction
        new_bill = Bill(
            status=data.status,
            bill_date=data.bill_date,
            total_amount=data.total_amount,
            user_id=data.user_id,
            shop_id=data.shop_id,
            image_url=data.image_url,
            image_hash=data.image_hash,
            image_expires_at=data.image_expires_at,
            image_status=data.image_status,
            error_message=data.error_message
        )

        # Persistence (Unit of Work)
        self.session.add(new_bill)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_bill)
        except IntegrityError as e:
            await self.session.rollback()
            raise e

        return new_bill

    async def update(self, bill_id: int, data: BillUpdate) -> Bill:
        bill = await self.get_by_id(bill_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return bill

        # User Existence Check (if user_id is being updated)
        if "user_id" in update_data and update_data["user_id"] != bill.user_id:
            await self._ensure_exists(model=User, field=User.id, value=update_data["user_id"], resource_name="User")

        # Shop Existence Check (if shop_id is being updated)
        if "shop_id" in update_data and update_data["shop_id"] != bill.shop_id:
            new_shop_id = update_data["shop_id"]
            if new_shop_id is not None:
                await self._ensure_exists(model=Shop, field=Shop.id, value=new_shop_id, resource_name="Shop")

        # Apply updates
        for key, value in update_data.items():
            setattr(bill, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(bill)
        except IntegrityError as e:
            await self.session.rollback()
            raise e

        return bill

    async def delete(self, bill_id: int) -> None:
        bill = await self.get_by_id(bill_id)
        
        self.session.delete(bill)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e

