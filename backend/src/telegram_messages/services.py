from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.services import AppService
from src.telegram_messages.models import TelegramMessage
from src.telegram_messages.schemas import TelegramMessageCreate, TelegramMessageUpdate
from src.common.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError
from src.users.models import User
from src.bills.models import Bill


class TelegramMessageService(AppService[TelegramMessage, TelegramMessageCreate, TelegramMessageUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=TelegramMessage, session=session)

    async def get_by_id(self, message_id: int) -> TelegramMessage:
        stmt = select(TelegramMessage).where(TelegramMessage.id == message_id)
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise ResourceNotFoundError("TelegramMessage", message_id)
        
        return message

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[TelegramMessage]:
        stmt = select(TelegramMessage).offset(skip).limit(limit).order_by(TelegramMessage.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _ensure_unique_telegram_message_id(self, telegram_message_id: int, exclude_id: Optional[int] = None) -> None:
        """
        Checks if a telegram_message_id already exists.
        Used to prevent duplicate telegram message IDs.
        """
        stmt = select(TelegramMessage).where(
            TelegramMessage.telegram_message_id == telegram_message_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(TelegramMessage.id != exclude_id)
        
        result = await self.session.execute(stmt)
        if result.scalars().first():
            raise ResourceAlreadyExistsError("TelegramMessage", "telegram_message_id", telegram_message_id)

    async def create(self, data: TelegramMessageCreate) -> TelegramMessage:
        # User Existence Check (Referential Integrity check before DB hit)
        await self._ensure_exists(model=User, field=User.id, value=data.user_id, resource_name="User")

        # Bill Existence Check (if provided)
        if data.bill_id:
            await self._ensure_exists(model=Bill, field=Bill.id, value=data.bill_id, resource_name="Bill")

        # Uniqueness Check (telegram_message_id)
        await self._ensure_unique_telegram_message_id(data.telegram_message_id)

        # Object Construction
        new_message = TelegramMessage(
            telegram_message_id=data.telegram_message_id,
            chat_id=data.chat_id,
            message_type=data.message_type,
            content=data.content,
            status=data.status,
            file_id=data.file_id,
            file_path=data.file_path,
            error_message=data.error_message,
            user_id=data.user_id,
            bill_id=data.bill_id
        )

        # Persistence (Unit of Work)
        self.session.add(new_message)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_message)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "telegram_message_id" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("TelegramMessage", "telegram_message_id", data.telegram_message_id) from e
            raise e

        return new_message

    async def update(self, message_id: int, data: TelegramMessageUpdate) -> TelegramMessage:
        message = await self.get_by_id(message_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return message

        # User Existence Check (if user_id is being updated)
        if "user_id" in update_data and update_data["user_id"] != message.user_id:
            await self._ensure_exists(model=User, field=User.id, value=update_data["user_id"], resource_name="User")

        # Bill Existence Check (if bill_id is being updated)
        if "bill_id" in update_data and update_data["bill_id"] != message.bill_id:
            new_bill_id = update_data["bill_id"]
            if new_bill_id is not None:
                await self._ensure_exists(model=Bill, field=Bill.id, value=new_bill_id, resource_name="Bill")

        # Uniqueness Check (if telegram_message_id is being updated)
        if "telegram_message_id" in update_data and update_data["telegram_message_id"] != message.telegram_message_id:
            await self._ensure_unique_telegram_message_id(update_data["telegram_message_id"], exclude_id=message.id)

        # Apply updates
        for key, value in update_data.items():
            setattr(message, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(message)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "telegram_message_id" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("TelegramMessage", "telegram_message_id", update_data.get("telegram_message_id", message.telegram_message_id)) from e
            raise e

        return message

    async def delete(self, message_id: int) -> None:
        message = await self.get_by_id(message_id)
        
        self.session.delete(message)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e
