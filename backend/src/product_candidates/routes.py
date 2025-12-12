from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from src.product_candidates.schemas import (
    ProductCandidateCreate,
    ProductCandidateUpdate,
    ProductCandidateResponse,
    ProductCandidateListResponse
)
from src.product_candidates.services import ProductCandidateService

router = APIRouter()


async def get_product_candidate_service(session: Annotated[AsyncSession, Depends(get_session)]) -> ProductCandidateService:
    """
    Dependency Injection factory dla ProductCandidateService.
    
    Most Koncepcyjny (Mentoring): W Symfony/Laravel, kontenery DI automatycznie rozwiązują zależności.
    W FastAPI, Depends() działa podobnie, ale jest bardziej deklaratywne - zależności są jawne
    na poziomie funkcji endpointu. To pozwala FastAPI zarządzać cyklem życia (np. session per-request)
    automatycznie dla każdego żądania.
    """
    return ProductCandidateService(session)


ServiceDependency = Annotated[ProductCandidateService, Depends(get_product_candidate_service)]


@router.get(
    "/",
    response_model=ProductCandidateListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all product candidates"
)
async def get_product_candidates(
    service: ServiceDependency,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Max number of items to return")
):
    """
    Pobiera listę product candidates z paginacją.
    
    Args:
        service: ProductCandidateService (wstrzyknięty przez DI)
        skip: Liczba elementów do pominięcia
        limit: Maksymalna liczba elementów do zwrócenia
        
    Returns:
        ProductCandidateListResponse: Paginowana lista product candidates
    """
    return await service.get_all(skip=skip, limit=limit)


@router.get(
    "/{product_candidate_id}",
    response_model=ProductCandidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product candidate by ID"
)
async def get_product_candidate(
    product_candidate_id: int,
    service: ServiceDependency
):
    """
    Pobiera product candidate po ID.
    
    Args:
        product_candidate_id: ID product candidate
        service: ProductCandidateService (wstrzyknięty przez DI)
        
    Returns:
        ProductCandidateResponse: Product candidate
        
    Raises:
        HTTPException 404: Jeśli product candidate nie istnieje
    """
    return await service.get_by_id(product_candidate_id)


@router.post(
    "/",
    response_model=ProductCandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product candidate"
)
async def create_product_candidate(
    data: ProductCandidateCreate,
    service: ServiceDependency
):
    """
    Tworzy nowy product candidate.
    
    Args:
        data: Dane do utworzenia product candidate
        service: ProductCandidateService (wstrzyknięty przez DI)
        
    Returns:
        ProductCandidateResponse: Utworzony product candidate
        
    Raises:
        HTTPException 404: Jeśli category_id lub product_index_id nie istnieją
    """
    return await service.create(data)


@router.patch(
    "/{product_candidate_id}",
    response_model=ProductCandidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a product candidate"
)
async def update_product_candidate(
    product_candidate_id: int,
    data: ProductCandidateUpdate,
    service: ServiceDependency
):
    """
    Aktualizuje product candidate.
    
    Args:
        product_candidate_id: ID product candidate do aktualizacji
        data: Dane do aktualizacji
        service: ProductCandidateService (wstrzyknięty przez DI)
        
    Returns:
        ProductCandidateResponse: Zaktualizowany product candidate
        
    Raises:
        HTTPException 404: Jeśli product candidate lub powiązanie nie istnieje
    """
    return await service.update(product_candidate_id, data)


@router.delete(
    "/{product_candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product candidate"
)
async def delete_product_candidate(
    product_candidate_id: int,
    service: ServiceDependency
):
    """
    Usuwa product candidate.
    
    Args:
        product_candidate_id: ID product candidate do usunięcia
        service: ProductCandidateService (wstrzyknięty przez DI)
        
    Raises:
        HTTPException 404: Jeśli product candidate nie istnieje
    """
    await service.delete(product_candidate_id)
    return None
