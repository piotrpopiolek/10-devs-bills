"""
FastAPI routes for categories endpoints.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.categories.schemas import CategoryListResponse, CategoryResponse
from src.categories.services import (
    get_categories,
    count_products_per_category,
    build_category_hierarchy,
    get_all_categories_for_hierarchy,
    validate_parent_category_exists,
    CategoryNotFoundError
)
from src.db.main import get_session
# TODO: Implement authentication dependency

# TODO dodanie agenta który będzie sprawdzał pod kątem najbardziej pozadanych cech programisty
# from src.deps import get_current_user
# from src.users.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=CategoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all product categories",
    description=(
        "Get a hierarchical list of all product categories with optional "
        "filtering by parent category. Supports including subcategories in "
        "the response for building complete category trees."
    ),
    responses={
        200: {
            "description": "Successfully retrieved categories",
            "content": {
                "application/json": {
                    "example": {
                        "categories": [
                            {
                                "id": 1,
                                "name": "Food & Beverages",
                                "parent_id": None,
                                "children": [],
                                "products_count": 150,
                                "created_at": "2024-01-01T00:00:00Z"
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Parent category with ID 999 does not exist"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - missing or invalid authentication token"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def get_categories_endpoint(
    parent_id: Optional[int] = Query(
        None,
        gt=0,
        description="Filter by parent category ID. Returns only direct children of the specified category."
    ),
    include_children: bool = Query(
        False,
        description="Include subcategories in response. When true, returns recursive hierarchical structure."
    ),
    # TODO: Add authentication when get_current_user is implemented
    # current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> CategoryListResponse:
    """
    Retrieve categories with optional filtering and hierarchical structure.
    
    This endpoint supports:
    - Filtering by parent category ID
    - Including subcategories in recursive structure
    - Counting products per category
    
    Args:
        parent_id: Optional parent category ID for filtering
        include_children: Whether to include subcategories
        session: Database session dependency
        
    Returns:
        CategoryListResponse with list of categories
        
    Raises:
        HTTPException: 400 if parent_id doesn't exist, 500 on server errors
    """
    try:
        # Guard clause: Validate parent_id exists if provided
        if parent_id is not None:
            try:
                await validate_parent_category_exists(session, parent_id)
            except CategoryNotFoundError as e:
                logger.warning(str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        # Fetch categories based on filters
        if include_children and parent_id is None:
            # For full hierarchy, fetch all categories
            categories = await get_all_categories_for_hierarchy(session)
        else:
            # Fetch filtered categories
            categories = await get_categories(
                session,
                parent_id=parent_id,
                include_children=include_children
            )
        
        # Early return: empty list if no categories found
        if not categories:
            return CategoryListResponse(categories=[])
        
        # Get all category IDs for product counting
        category_ids = [cat.id for cat in categories]
        
        # Count products for all categories in one query (optimization)
        products_count_map = await count_products_per_category(
            session,
            category_ids
        )
        
        # Build response
        if include_children:
            # Build hierarchical structure
            category_responses = build_category_hierarchy(
                categories,
                products_count_map,
                include_children=True
            )
        else:
            # Flat structure without children
            category_responses = [
                CategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    parent_id=cat.parent_id,
                    children=[],
                    products_count=products_count_map.get(cat.id, 0),
                    created_at=cat.created_at
                )
                for cat in categories
            ]
        
        return CategoryListResponse(categories=category_responses)
        
    except ValueError as e:
        # Handle cycle detection or depth exceeded errors
        logger.error(
            f"Error building category hierarchy: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error building category hierarchy. Please contact support."
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Unexpected error in GET /categories: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
