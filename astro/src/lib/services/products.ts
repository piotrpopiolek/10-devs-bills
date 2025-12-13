import type { ProductsQueryParams, ProductListResponse, ApiResponse } from '../../types';
import { apiFetch } from '../api-client';

export const getProducts = async (params: ProductsQueryParams): Promise<ProductListResponse> => {
  const queryParams = new URLSearchParams();
  
  if (params.search) {
    queryParams.append('search', params.search);
  }
  
  if (params.category_id !== undefined) {
    queryParams.append('category_id', params.category_id.toString());
  }
  
  // Default limit to 20 if not specified
  const limit = params.limit || 20;
  queryParams.append('limit', limit.toString());
  
  // Use skip directly (default to 0)
  const skip = params.skip ?? 0;
  queryParams.append('skip', skip.toString());

  try {
    const response = await apiFetch(`/api/products?${queryParams.toString()}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<ProductListResponse> | ProductListResponse = await response.json();
    
    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
        if (!data.success) {
            throw new Error(data.message || 'Failed to fetch products');
        }
        return data.data;
    }
    
    return data as ProductListResponse;
  } catch (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
};

