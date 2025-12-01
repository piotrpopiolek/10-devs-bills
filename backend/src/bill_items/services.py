from typing import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.common.services import AppService
from src.bill_items.models import BillItem
from src.bill_items.schemas import BillItemCreate, BillItemUpdate
from src.common.exceptions import ResourceNotFoundError
from src.bills.models import Bill
from src.product_indexes.models import ProductIndex


class BillItemService(AppService):

    async def get_by_id(self, bill_item_id: int) -> BillItem:
        stmt = select(BillItem).where(BillItem.id == bill_item_id)
        result = await self.session.execute(stmt)
        bill_item = result.scalar_one_or_none()

        if not bill_item:
            raise ResourceNotFoundError("BillItem", bill_item_id)
        
        return bill_item

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[BillItem]:
        stmt = select(BillItem).offset(skip).limit(limit).order_by(BillItem.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: BillItemCreate) -> BillItem:
        # Bill Existence Check (Referential Integrity check before DB hit)
        await self._ensure_exists(model=Bill, field=Bill.id, value=data.bill_id, resource_name="Bill")

        # ProductIndex Existence Check (if provided)
        if data.index_id:
            await self._ensure_exists(model=ProductIndex, field=ProductIndex.id, value=data.index_id, resource_name="ProductIndex")

        # Object Construction
        new_bill_item = BillItem(
            quantity=data.quantity,
            unit_price=data.unit_price,
            total_price=data.total_price,
            is_verified=data.is_verified,
            verification_source=data.verification_source,
            bill_id=data.bill_id,
            index_id=data.index_id,
            original_text=data.original_text,
            confidence_score=data.confidence_score
        )

        # Persistence (Unit of Work)
        self.session.add(new_bill_item)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_bill_item)
        except IntegrityError as e:
            await self.session.rollback()
            raise e

        return new_bill_item

    async def update(self, bill_item_id: int, data: BillItemUpdate) -> BillItem:
        bill_item = await self.get_by_id(bill_item_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return bill_item

        # Bill Existence Check (if bill_id is being updated)
        if "bill_id" in update_data and update_data["bill_id"] != bill_item.bill_id:
            await self._ensure_exists(model=Bill, field=Bill.id, value=update_data["bill_id"], resource_name="Bill")

        # ProductIndex Existence Check (if index_id is being updated)
        if "index_id" in update_data and update_data["index_id"] != bill_item.index_id:
            new_index_id = update_data["index_id"]
            if new_index_id is not None:
                await self._ensure_exists(model=ProductIndex, field=ProductIndex.id, value=new_index_id, resource_name="ProductIndex")

        # Apply updates
        for key, value in update_data.items():
            setattr(bill_item, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(bill_item)
        except IntegrityError as e:
            await self.session.rollback()
            raise e

        return bill_item

    async def delete(self, bill_item_id: int) -> None:
        bill_item = await self.get_by_id(bill_item_id)
        
        self.session.delete(bill_item)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e

