from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
# from app.models.user import User
 
# async def get_current_user(
#     db: AsyncSession = Depends(get_session),
#     # JWT token from header
# ) -> User:
#     # Implementacja autoryzacji
#     pass