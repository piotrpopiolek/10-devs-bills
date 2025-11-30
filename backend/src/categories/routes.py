from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from src.categories.schemas import (
    CategoryCreate, 
    CategoryUpdate, 
    CategoryResponse, 
    CategoryListResponse
)
from src.categories.services import CategoryService

router = APIRouter()

async def get_category_service(session: Annotated[AsyncSession, Depends(get_session)]) -> CategoryService:
    return CategoryService(session)

ServiceDependency = Annotated[CategoryService, Depends(get_category_service)]

@router.get("/", response_model=list[CategoryListResponse], status_code=status.HTTP_200_OK, summary="List all categories")
async def get_categories(service: ServiceDependency, skip: int = Query(0, ge=0, description="Number of items to skip"), limit: int = Query(100, ge=1, le=100, description="Max number of items to return")):
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK, summary="Get category by ID")
async def get_category(category_id: int, service: ServiceDependency):
    return await service.get_by_id(category_id)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Create a new category")
async def create_category(data: CategoryCreate, service: ServiceDependency):
    return await service.create(data)


@router.patch("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK, summary="Update a category")
async def update_category(category_id: int, data: CategoryUpdate, service: ServiceDependency):
    return await service.update(category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT,summary="Delete a category")
async def delete_category(category_id: int, service: ServiceDependency):
    await service.delete(category_id)
    return None