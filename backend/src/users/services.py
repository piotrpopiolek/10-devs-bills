from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.services import AppService
from src.users.models import User
from src.users.schemas import UserCreate, UserUpdate
from src.common.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


class UserService(AppService[User, UserCreate, UserUpdate]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=User, session=session)

    async def get_by_id(self, user_id: int) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundError("User", user_id)
        
        return user

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        stmt = select(User).offset(skip).limit(limit).order_by(User.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _ensure_unique_external_id(self, external_id: int, exclude_id: Optional[int] = None) -> None:
        """
        Checks if an external_id already exists.
        Used to prevent duplicate Telegram user IDs.
        """
        stmt = select(User).where(
            User.external_id == external_id
        )
        
        if exclude_id is not None:
            stmt = stmt.where(User.id != exclude_id)
        
        result = await self.session.execute(stmt)
        if result.scalars().first():
            raise ResourceAlreadyExistsError("User", "external_id", external_id)

    async def create(self, data: UserCreate) -> User:
        # Uniqueness Check (external_id)
        await self._ensure_unique_external_id(data.external_id)

        # Object Construction
        new_user = User(
            external_id=data.external_id,
            is_active=data.is_active
        )

        # Persistence (Unit of Work)
        self.session.add(new_user)
        
        try:
            await self.session.commit()
            await self.session.refresh(new_user)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "external_id" in str(e.orig) or "idx_users_external_id" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("User", "external_id", data.external_id) from e
            raise e

        return new_user

    async def update(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id)

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return user

        # Uniqueness Check (if external_id is being updated)
        if "external_id" in update_data and update_data["external_id"] != user.external_id:
            await self._ensure_unique_external_id(update_data["external_id"], exclude_id=user.id)

        # Apply updates
        for key, value in update_data.items():
            setattr(user, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation
            if "external_id" in str(e.orig) or "idx_users_external_id" in str(e.orig) or "23505" in str(e.orig):
                raise ResourceAlreadyExistsError("User", "external_id", update_data.get("external_id", user.external_id)) from e
            raise e

        return user

    async def delete(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        
        self.session.delete(user)
        
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise e

