import type { ProductCandidatesQueryParams, ProductCandidateListResponse, ProductCandidateResponse, CreateProductCandidateCommand, UpdateProductCandidateCommand, ApiResponse } from '../../types';
import { apiFetch } from '../api-client';

const API_BASE = '/api/product-candidates';

export const getProductCandidates = async (params: ProductCandidatesQueryParams): Promise<ProductCandidateListResponse> => {
  const queryParams = new URLSearchParams();
  
  if (params.search) {
    queryParams.append('search', params.search);
  }
  
  if (params.status) {
    queryParams.append('status', params.status);
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
    const response = await apiFetch(`${API_BASE}?${queryParams.toString()}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<ProductCandidateListResponse> | ProductCandidateListResponse = await response.json();
    
    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
        if (!data.success) {
            throw new Error(data.message || 'Failed to fetch product candidates');
        }
        return data.data;
    }
    
    return data as ProductCandidateListResponse;
  } catch (error) {
    console.error('Error fetching product candidates:', error);
    throw error;
  }
};

export const getProductCandidate = async (id: number): Promise<ProductCandidateResponse> => {
  try {
    const response = await apiFetch(`${API_BASE}/${id}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<ProductCandidateResponse> | ProductCandidateResponse = await response.json();
    
    if ('data' in data && 'success' in data) {
        if (!data.success) {
            throw new Error(data.message || 'Failed to fetch product candidate');
        }
        return data.data;
    }
    
    return data as ProductCandidateResponse;
  } catch (error) {
    console.error('Error fetching product candidate:', error);
    throw error;
  }
};

export const createProductCandidate = async (data: CreateProductCandidateCommand): Promise<ProductCandidateResponse> => {
  try {
    const response = await apiFetch(API_BASE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result: ApiResponse<ProductCandidateResponse> | ProductCandidateResponse = await response.json();
    
    if ('data' in result && 'success' in result) {
        if (!result.success) {
            throw new Error(result.message || 'Failed to create product candidate');
        }
        return result.data;
    }
    
    return result as ProductCandidateResponse;
  } catch (error) {
    console.error('Error creating product candidate:', error);
    throw error;
  }
};

export const updateProductCandidate = async (id: number, data: UpdateProductCandidateCommand): Promise<ProductCandidateResponse> => {
  try {
    const response = await apiFetch(`${API_BASE}/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result: ApiResponse<ProductCandidateResponse> | ProductCandidateResponse = await response.json();
    
    if ('data' in result && 'success' in result) {
        if (!result.success) {
            throw new Error(result.message || 'Failed to update product candidate');
        }
        return result.data;
    }
    
    return result as ProductCandidateResponse;
  } catch (error) {
    console.error('Error updating product candidate:', error);
    throw error;
  }
};

export const deleteProductCandidate = async (id: number): Promise<void> => {
  try {
    const response = await apiFetch(`${API_BASE}/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
  } catch (error) {
    console.error('Error deleting product candidate:', error);
    throw error;
  }
};
