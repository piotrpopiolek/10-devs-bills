from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from src.users.schemas import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserListResponse
)
from src.users.services import UserService

router = APIRouter()

async def get_user_service(session: Annotated[AsyncSession, Depends(get_session)]) -> UserService:
    return UserService(session)

ServiceDependency = Annotated[UserService, Depends(get_user_service)]

@router.get("/", response_model=UserListResponse, status_code=status.HTTP_200_OK, summary="List all users")
async def get_users(service: ServiceDependency, skip: int = Query(0, ge=0, description="Number of items to skip"), limit: int = Query(100, ge=1, le=100, description="Max number of items to return")):
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK, summary="Get user by ID")
async def get_user(user_id: int, service: ServiceDependency):
    return await service.get_by_id(user_id)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def create_user(data: UserCreate, service: ServiceDependency):
    return await service.create(data)


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK, summary="Update a user")
async def update_user(user_id: int, data: UserUpdate, service: ServiceDependency):
    return await service.update(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
async def delete_user(user_id: int, service: ServiceDependency):
    await service.delete(user_id)
    return None

