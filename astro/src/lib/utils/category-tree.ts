import type { CategoryResponse, CategoryTreeNode } from '@/types';

/**
 * Transforms a flat list of categories into a hierarchical tree structure.
 * 
 * @param categories - Flat list of categories with parent_id references
 * @returns Array of root categories (categories with parent_id === null) with their children
 */
export function buildCategoryTree(
  categories: CategoryResponse[]
): CategoryTreeNode[] {
  // 1. Create a map of categories by ID for quick access
  const categoryMap = new Map<number, CategoryTreeNode>();
  const rootCategories: CategoryTreeNode[] = [];

  // 2. Convert all categories to CategoryTreeNode with empty children array
  categories.forEach((cat) => {
    categoryMap.set(cat.id, {
      id: cat.id,
      name: cat.name,
      parent_id: cat.parent_id,
      created_at: cat.created_at,
      products_count: cat.products_count,
      bill_items_count: cat.bill_items_count,
      children: [],
    });
  });

  // 3. Build parent-child relationships
  categories.forEach((cat) => {
    const node = categoryMap.get(cat.id);
    if (!node) return; // Safety check, should not happen
    
    if (cat.parent_id === null) {
      // Root category
      rootCategories.push(node);
    } else {
      // Child category - find parent and add to its children
      const parent = categoryMap.get(cat.parent_id);
      if (parent) {
        parent.children.push(node);
      } else {
        // Parent not found - treat as root (orphaned category)
        rootCategories.push(node);
      }
    }
  });

  // 4. Sort children alphabetically (recursive)
  const sortChildren = (node: CategoryTreeNode) => {
    node.children.sort((a, b) => a.name.localeCompare(b.name));
    node.children.forEach(sortChildren);
  };
  rootCategories.forEach(sortChildren);

  return rootCategories;
}

