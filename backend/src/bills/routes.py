from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from src.deps import CurrentUser
from src.middleware.rate_limit import check_monthly_bills_limit
from src.bills.schemas import (
    BillCreate, 
    BillUpdate, 
    BillResponse, 
    BillListResponse
)
from src.bills.services import BillService

router = APIRouter()

async def get_bill_service(session: Annotated[AsyncSession, Depends(get_session)]) -> BillService:
    return BillService(session)

ServiceDependency = Annotated[BillService, Depends(get_bill_service)]

@router.get("/", response_model=BillListResponse, status_code=status.HTTP_200_OK, summary="List all bills")
async def get_bills(service: ServiceDependency, skip: int = Query(0, ge=0, description="Number of items to skip"), limit: int = Query(100, ge=1, le=100, description="Max number of items to return")):
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{bill_id}", response_model=BillResponse, status_code=status.HTTP_200_OK, summary="Get bill by ID")
async def get_bill(bill_id: int, service: ServiceDependency):
    return await service.get_by_id(bill_id)


@router.post("/", response_model=BillResponse, status_code=status.HTTP_201_CREATED, summary="Create a new bill", dependencies=[Depends(check_monthly_bills_limit)])
async def create_bill(data: BillCreate, service: ServiceDependency, user: CurrentUser):
    # Enforce user isolation: user_id from token takes precedence
    data.user_id = user.id
    return await service.create(data)


@router.patch("/{bill_id}", response_model=BillResponse, status_code=status.HTTP_200_OK, summary="Update a bill")
async def update_bill(bill_id: int, data: BillUpdate, service: ServiceDependency):
    return await service.update(bill_id, data)


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a bill")
async def delete_bill(bill_id: int, service: ServiceDependency):
    await service.delete(bill_id)
    return None
