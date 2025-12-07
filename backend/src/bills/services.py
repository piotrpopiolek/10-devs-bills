from typing import Any
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.common.services import AppService
from src.bills.models import Bill
from src.bills.schemas import BillCreate, BillUpdate, BillResponse
from src.common.exceptions import ResourceNotFoundError
from src.users.models import User
from src.shops.models import Shop
from src.storage.service import StorageService


class BillService(AppService[Bill, BillCreate, BillUpdate]):
    def __init__(self, session: AsyncSession, storage_service: StorageService):
        super().__init__(model=Bill, session=session)
        self.storage_service = storage_service

    def _to_response(self, bill: Bill) -> BillResponse:
        """
        Convert Bill model to BillResponse schema with signed URL.
        
        This method encapsulates the logic for generating signed URLs
        and converting Bill models to BillResponse schemas, following
        the DRY principle to avoid code duplication.
        
        Args:
            bill: The Bill model instance to convert
            
        Returns:
            BillResponse with image_signed_url populated if image_url exists
        """
        image_signed_url = None
        if bill.image_url:
            image_signed_url = self.storage_service.get_signed_url(bill.image_url)
        
        response = BillResponse.model_validate(bill, from_attributes=True)
        response.image_signed_url = image_signed_url
        return response

    async def create(self, data: BillCreate) -> BillResponse:
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

        return self._to_response(new_bill)

    async def update(self, bill_id: int, data: BillUpdate) -> BillResponse:
        # Use super().get_by_id() to get Bill model, not BillResponse
        bill = await super().get_by_id(bill_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            # Even if no updates, return BillResponse with signed URL
            return self._to_response(bill)

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

        return self._to_response(bill)

    async def get_by_id(self, bill_id: int) -> BillResponse:
        """
        Get bill by ID and generate signed URL for the image.
        Overrides base method to add image_signed_url to response.
        """
        bill = await super().get_by_id(bill_id)
        return self._to_response(bill)

    async def get_all(self, skip: int = 0, limit: int = 100) -> dict[str, Any]:
        """
        Get all bills with pagination and generate signed URLs for images.
        Overrides base method to add image_signed_url to each bill.
        """
        result = await super().get_all(skip=skip, limit=limit)
        
        # Generate signed URLs for each bill
        bills_with_urls = [
            self._to_response(bill) for bill in result["items"]
        ]
        
        return {
            "items": bills_with_urls,
            "total": result["total"],
            "skip": result["skip"],
            "limit": result["limit"]
        }

    async def delete(self, bill_id: int) -> None:
        # Use super().get_by_id() to get Bill model, not BillResponse
        bill = await super().get_by_id(bill_id)
        
        self.session.delete(bill)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e

