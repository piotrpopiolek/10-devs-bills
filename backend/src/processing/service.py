"""
Bills Processing Service.

Orchestrates the complete bill processing pipeline from file download to database storage.
"""
import logging
from io import BytesIO
from typing import Optional
from decimal import Decimal
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.bills.models import Bill, ProcessingStatus
from src.common.exceptions import ResourceNotFoundError
from src.bills.services import BillService
from src.bills.schemas import BillUpdate
from src.bill_items.models import BillItem, VerificationSource
from src.bill_items.services import BillItemService
from src.bill_items.schemas import BillItemCreate
from src.shops.services import ShopService
from src.storage.service import StorageService
from src.ocr.services import OCRService
from src.ocr.schemas import OCRReceiptData
from src.processing.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class BillsProcessorService:
    """
    Service orchestrating bill processing pipeline.

    Flow:
    1. Download file from Storage
    2. Call OCR Service
    3. Update Bill status → PROCESSING
    4. Get or create Shop
    5. Create BillItems
    6. Update Bill (total_amount, shop_id, status → COMPLETED)
    7. Handle errors (status → ERROR, error_message)
    """

    def __init__(
        self,
        session: AsyncSession,
        storage_service: StorageService,
        ocr_service: OCRService,
        bill_service: BillService,
        bill_item_service: BillItemService,
        shop_service: ShopService
    ):
        self.session = session
        self.storage_service = storage_service
        self.ocr_service = ocr_service
        self.bill_service = bill_service
        self.bill_item_service = bill_item_service
        self.shop_service = shop_service

    async def process_receipt(self, bill_id: int) -> None:
        """
        Main method processing receipt from PENDING to COMPLETED/ERROR.

        IMPORTANT:
        Operations are NOT atomic in terms of database transaction because underlying
        services (BillService, BillItemService) perform their own commits.
        We rely on optimistic concurrency and explicit error handling state updates.
        
        Args:
            bill_id: ID of the Bill to process

        Raises:
            ResourceNotFoundError: If bill doesn't exist (propagated from BillService)
        """
        logger.info(f"Starting receipt processing for bill_id={bill_id}")

        try:
            # Step 1: Get Bill and validate status
            bill = await self._get_bill(bill_id)

            if bill.status != ProcessingStatus.PENDING:
                if bill.status == ProcessingStatus.COMPLETED:
                    logger.info(f"Bill {bill_id} already processed (COMPLETED), skipping")
                elif bill.status == ProcessingStatus.ERROR:
                    logger.warning(f"Bill {bill_id} previously failed (ERROR), retrying...")
                else:
                    logger.warning(f"Bill {bill_id} is in status {bill.status}, skipping")
                return

            if not bill.image_url:
                await self._set_error(bill_id, "Bill has no image_url")
                return

            # Step 2: Download file from Storage
            file_content = await self._download_file(bill.image_url)

            # Step 3: Update Bill status → PROCESSING
            await self._update_bill_status(bill_id, ProcessingStatus.PROCESSING)

            # Step 4: Call OCR Service
            ocr_data = await self._extract_receipt_data(file_content, bill.image_url)

            # Step 5: Get or create Shop
            shop_id = await self._get_or_create_shop(
                ocr_data.shop_name,
                ocr_data.shop_address
            )

            # Step 6: Create BillItems
            await self._create_bill_items(bill_id, ocr_data)

            # Step 7: Update Bill → COMPLETED
            await self._update_bill_completed(
                bill_id,
                total_amount=ocr_data.total_amount,
                shop_id=shop_id,
                bill_date=ocr_data.date or bill.bill_date
            )

            logger.info(f"Receipt processing completed for bill_id={bill_id}")

        except Exception as e:
            logger.error(f"Error processing receipt bill_id={bill_id}: {e}", exc_info=True)
            # Try to save error state
            try:
                await self._set_error(bill_id, str(e))
            except Exception as inner_e:
                logger.critical(f"CRITICAL: Failed to save error status for bill {bill_id}: {inner_e}", exc_info=True)
            
            # Re-raise to let caller know something went wrong
            raise

    async def _get_bill(self, bill_id: int) -> Bill:
        """
        Get Bill model by ID, raise ResourceNotFoundError if not found.

        Używa bezpośredniego zapytania SQLAlchemy, ponieważ potrzebujemy modelu,
        a nie response schema (BillResponse).
        """
        stmt = select(Bill).where(Bill.id == bill_id)
        result = await self.session.execute(stmt)
        bill = result.scalar_one_or_none()

        if not bill:
            raise ResourceNotFoundError("Bill", bill_id)

        return bill

    async def _download_file(self, image_url: str) -> bytes:
        """
        Download file from Storage.
        Propagates StorageService exceptions.
        """
        file_content = await self.storage_service.download_file(image_url)
        logger.debug(f"Downloaded file: {image_url} ({len(file_content)} bytes)")
        return file_content

    async def _extract_receipt_data(self, file_content: bytes, filename: str) -> OCRReceiptData:
        """
        Extract receipt data using OCR Service.
        Propagates OCRService exceptions.
        """
        file_obj = BytesIO(file_content)

        # Determine MIME type from filename
        mime_type = "image/jpeg"  # default
        if filename.endswith(".png"):
            mime_type = "image/png"
        elif filename.endswith(".webp"):
            mime_type = "image/webp"

        # Create UploadFile
        upload_file = UploadFile(
            file=file_obj,
            filename=filename,
            headers={"content-type": mime_type}
        )

        # Call OCR Service
        ocr_data = await self.ocr_service.extract_data(upload_file)
        logger.info(f"OCR extraction successful: {len(ocr_data.items)} items")
        return ocr_data

    async def _update_bill_status(self, bill_id: int, status: ProcessingStatus) -> None:
        """Update Bill status."""
        bill = await self._get_bill(bill_id)

        update_data = BillUpdate(status=status)

        try:
            await self.bill_service.update(bill_id, update_data, bill.user_id)
            logger.debug(f"Updated bill {bill_id} status to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update bill status: {e}", exc_info=True)
            raise ProcessingError(f"Failed to update bill status: {str(e)}") from e

    async def _get_or_create_shop(
        self,
        shop_name: Optional[str],
        shop_address: Optional[str]
    ) -> Optional[int]:
        """Get or create Shop, return shop_id or None."""
        if not shop_name:
            logger.debug("No shop name in OCR data, skipping shop creation")
            return None

        try:
            shop = await self.shop_service.get_or_create_by_name(
                name=shop_name,
                address=shop_address
            )
            logger.info(f"Shop resolved: {shop.id} ({shop_name})")
            return shop.id
        except Exception as e:
            logger.error(f"Failed to get/create shop: {e}", exc_info=True)
            # Don't fail processing if shop creation fails
            # Just log and continue without shop_id
            logger.warning(f"Continuing without shop_id due to error: {e}")
            return None

    async def _create_bill_items(self, bill_id: int, ocr_data: OCRReceiptData) -> None:
        """
        Create BillItems from OCR data.
        Validates data via Pydantic before DB insertion.
        """
        if not ocr_data.items:
            logger.warning(f"No items in OCR data for bill_id={bill_id}")
            return

        created_count = 0
        for ocr_item in ocr_data.items:
            try:
                # Determine if item needs verification (confidence < 0.8)
                needs_verification = ocr_item.confidence_score < 0.8

                # Calculate unit_price if not provided
                unit_price = ocr_item.unit_price
                if unit_price is None:
                    # Calculate from total_price and quantity
                    if ocr_item.quantity > 0:
                        unit_price = ocr_item.total_price / ocr_item.quantity
                    else:
                        logger.warning(
                            f"Invalid quantity for item {ocr_item.name}: {ocr_item.quantity}, "
                            f"skipping bill_item creation"
                        )
                        continue

                # Pydantic validation (BillItemCreate has strict=True via AppBaseModel)
                bill_item_data = BillItemCreate(
                    bill_id=bill_id,
                    quantity=ocr_item.quantity,
                    unit_price=unit_price,
                    total_price=ocr_item.total_price,
                    original_text=ocr_item.name,
                    confidence_score=Decimal(str(ocr_item.confidence_score)),
                    is_verified=not needs_verification,  # Auto-verified if confidence >= 0.8
                    verification_source=VerificationSource.AUTO
                )

                await self.bill_item_service.create(bill_item_data)
                created_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to create bill_item for bill_id={bill_id}, "
                    f"item={ocr_item.name}: {e}",
                    exc_info=True
                )
                # Continue with other items even if one fails
                continue

        logger.info(f"Created {created_count}/{len(ocr_data.items)} bill_items for bill_id={bill_id}")

    async def _update_bill_completed(
        self,
        bill_id: int,
        total_amount: Decimal,
        shop_id: Optional[int],
        bill_date: datetime
    ) -> None:
        """Update Bill with final data and set status to COMPLETED."""
        bill = await self._get_bill(bill_id)

        update_data = BillUpdate(
            status=ProcessingStatus.COMPLETED,
            total_amount=total_amount,
            shop_id=shop_id,
            bill_date=bill_date
        )

        try:
            await self.bill_service.update(bill_id, update_data, bill.user_id)
            logger.info(f"Bill {bill_id} marked as COMPLETED")
        except Exception as e:
            logger.error(f"Failed to update bill as completed: {e}", exc_info=True)
            raise ProcessingError(f"Failed to finalize bill: {str(e)}") from e

    async def _set_error(self, bill_id: int, error_message: str) -> None:
        """Set Bill status to ERROR and save error message."""
        bill = await self._get_bill(bill_id)

        # Truncate error message to fit database field
        max_error_length = 1000
        truncated_error = (
            error_message[:max_error_length]
            if len(error_message) > max_error_length
            else error_message
        )

        update_data = BillUpdate(
            status=ProcessingStatus.ERROR,
            error_message=truncated_error
        )

        try:
            await self.bill_service.update(bill_id, update_data, bill.user_id)
            logger.error(f"Bill {bill_id} marked as ERROR: {truncated_error}")
        except Exception as e:
            logger.critical(
                f"CRITICAL: Failed to set error status for bill {bill_id}: {e}",
                exc_info=True
            )
