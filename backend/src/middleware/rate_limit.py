from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.deps import CurrentUser, get_session
from src.users.services import UserService
from src.config import settings

async def check_monthly_bills_limit(
    user: CurrentUser,
    session: AsyncSession = Depends(get_session)
) -> None:
    """
    Dependency to check if the user has reached their monthly bills limit.
    Raises 429 Too Many Requests if the limit is exceeded.
    """
    user_service = UserService(session)
    stats = await user_service.get_user_usage_stats(user.id)
    
    if stats["remaining_bills"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Osiągnięto miesięczny limit {settings.MONTHLY_BILLS_LIMIT} paragonów. Limit zresetuje się w przyszłym miesiącu."
        )

