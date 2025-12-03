import type { CategoriesQueryParams, CategoryListResponse, ApiResponse } from '../../types';

export const getCategories = async (params: CategoriesQueryParams = {}): Promise<CategoryListResponse> => {
  const queryParams = new URLSearchParams();
  
  // Default limit to 100 if not specified (backend default)
  const limit = params.limit || 100;
  queryParams.append('limit', limit.toString());
  
  // Use skip directly (default to 0)
  const skip = params.skip ?? 0;
  queryParams.append('skip', skip.toString());

  try {
    const response = await fetch(`/api/categories?${queryParams.toString()}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<CategoryListResponse> | CategoryListResponse = await response.json();
    
    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
        if (!data.success) {
            throw new Error(data.message || 'Failed to fetch categories');
        }
        return data.data;
    }
    
    return data as CategoryListResponse;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
};

