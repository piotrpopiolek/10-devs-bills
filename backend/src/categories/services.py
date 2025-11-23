"""
Business logic layer for categories operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict
from src.categories.models import Category
from src.product_indexes.models import ProductIndex
from src.categories.schemas import CategoryResponse


class CategoryNotFoundError(Exception):
    """Raised when a category is not found in the database."""
    pass


async def validate_parent_category_exists(
    session: AsyncSession,
    parent_id: int
) -> Category:
    """
    Validate that a parent category exists in the database.
    
    Args:
        session: Database session
        parent_id: Parent category ID to validate
        
    Returns:
        Category model if found
        
    Raises:
        CategoryNotFoundError: If parent category does not exist
    """
    parent_category = await session.get(Category, parent_id)
    if not parent_category:
        raise CategoryNotFoundError(f"Parent category with ID {parent_id} does not exist")
    return parent_category


async def get_categories(
    session: AsyncSession,
    parent_id: Optional[int] = None,
    include_children: bool = False
) -> List[Category]:
    """
    Fetch categories from database with optional filtering and eager loading.
    
    Args:
        session: Database session
        parent_id: Optional parent category ID for filtering
        include_children: Whether to eager load children relationships
        
    Returns:
        List of Category models
    """
    query = select(Category)
    
    # Filter by parent_id
    if parent_id is not None:
        query = query.where(Category.parent_id == parent_id)
    else:
        # Only root categories (parent_id is NULL)
        query = query.where(Category.parent_id.is_(None))
    
    # Eager loading for children if needed
    if include_children:
        query = query.options(selectinload(Category.children))
    
    # Execute query
    result = await session.execute(query)
    categories = result.scalars().all()
    
    return categories


async def count_products_per_category(
    session: AsyncSession,
    category_ids: List[int]
) -> Dict[int, int]:
    """
    Count products (indexes) for each category in a single optimized query.
    
    This function avoids N+1 queries by using a single aggregation query
    with GROUP BY.
    
    Args:
        session: Database session
        category_ids: List of category IDs to count products for
        
    Returns:
        Dictionary mapping category_id to products_count
    """
    if not category_ids:
        return {}
    
    # Single query with GROUP BY to count products per category
    query = (
        select(
            Index.category_id,
            func.count(Index.id).label('count')
        )
        .where(Index.category_id.in_(category_ids))
        .group_by(Index.category_id)
    )
    
    result = await session.execute(query)
    
    # Build dictionary: {category_id: count}
    products_count_map = {
        row.category_id: row.count
        for row in result
    }
    
    # Ensure all category_ids are in the map (with 0 if no products)
    return {
        category_id: products_count_map.get(category_id, 0)
        for category_id in category_ids
    }


def build_category_hierarchy(
    categories: List[Category],
    products_count_map: Dict[int, int],
    include_children: bool = False,
    max_depth: int = 10
) -> List[CategoryResponse]:
    """
    Recursively build hierarchical category structure from flat list.
    
    This function builds a tree structure from categories, handling
    parent-child relationships and counting products recursively.
    
    Args:
        categories: List of Category models (may include children via eager loading)
        products_count_map: Dictionary mapping category_id to products_count
        include_children: Whether to include subcategories in response
        max_depth: Maximum recursion depth to prevent infinite loops
        
    Returns:
        List of CategoryResponse objects with hierarchical structure
        
    Raises:
        ValueError: If maximum depth is exceeded (indicates cycle in hierarchy)
    """
    # Map categories by ID for quick lookup
    category_map = {cat.id: cat for cat in categories}
    
    # Track visited categories to detect cycles
    visited = set()
    
    def build_tree(category: Category, depth: int = 0) -> CategoryResponse:
        """
        Recursively build category tree.
        
        Args:
            category: Category model to process
            depth: Current recursion depth
            
        Returns:
            CategoryResponse with children populated
        """
        # Guard clause: prevent infinite recursion
        if depth > max_depth:
            raise ValueError(f"Maximum category depth ({max_depth}) exceeded. Possible cycle detected.")
        
        # Guard clause: detect cycles
        if category.id in visited:
            raise ValueError(f"Cycle detected in category hierarchy at category ID {category.id}")
        
        visited.add(category.id)
        
        # Build children list if include_children is True
        children = []
        if include_children:
            # Use eager-loaded children relationship
            for child in category.children:
                try:
                    child_response = build_tree(child, depth + 1)
                    children.append(child_response)
                except ValueError as e:
                    # Re-raise cycle detection errors
                    raise e
        
        # Get products count for this category
        products_count = products_count_map.get(category.id, 0)
        
        # Remove from visited after processing (for siblings)
        visited.remove(category.id)
        
        return CategoryResponse(
            id=category.id,
            name=category.name,
            parent_id=category.parent_id,
            children=children,
            products_count=products_count,
            created_at=category.created_at
        )
    
    # Build tree for root categories (parent_id is None)
    root_categories = [cat for cat in categories if cat.parent_id is None]
    
    return [build_tree(cat) for cat in root_categories]


async def get_all_categories_for_hierarchy(
    session: AsyncSession
) -> List[Category]:
    """
    Fetch all categories from database for building complete hierarchy.
    
    This is used when include_children=True to get all categories
    needed for building the full tree structure.
    
    Args:
        session: Database session
        
    Returns:
        List of all Category models with children eagerly loaded
    """
    query = (
        select(Category)
        .options(selectinload(Category.children))
    )
    
    result = await session.execute(query)
    return result.scalars().unique().all()

