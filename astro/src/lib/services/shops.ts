import type { ShopsQueryParams, ShopListResponse, ApiResponse } from '../../types';
import { apiFetch } from '../api-client';

export const getShops = async (params: ShopsQueryParams): Promise<ShopListResponse> => {
  const queryParams = new URLSearchParams();
  
  if (params.search) {
    queryParams.append('search', params.search);
  }
  
  // Default limit to 10 if not specified
  const limit = params.limit || 10;
  queryParams.append('limit', limit.toString());
  
  // Use skip directly (default to 0)
  const skip = params.skip ?? 0;
  queryParams.append('skip', skip.toString());

  try {
    const response = await apiFetch(`/api/shops?${queryParams.toString()}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<ShopListResponse> | ShopListResponse = await response.json();
    
    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
        if (!data.success) {
            throw new Error(data.message || 'Failed to fetch shops');
        }
        return data.data;
    }
    
    return data as ShopListResponse;
  } catch (error) {
    console.error('Error fetching shops:', error);
    throw error;
  }
};

