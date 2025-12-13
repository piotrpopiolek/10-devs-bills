import type { BillsQueryParams, BillListResponse, ApiResponse, BillResponse, BillItemListResponse, PendingVerificationQueryParams } from '../../types';
import { apiFetch } from '../api-client';

export const getBills = async (params: BillsQueryParams): Promise<BillListResponse> => {
  const queryParams = new URLSearchParams();
  
  // Default limit to 20 if not specified
  const limit = params.limit || 20;
  queryParams.append('limit', limit.toString());
  
  // Use skip directly (default to 0)
  const skip = params.skip ?? 0;
  queryParams.append('skip', skip.toString());
  
  if (params.status) {
    queryParams.append('status', params.status);
  }
  
  if (params.shop_id !== undefined) {
    queryParams.append('shop_id', params.shop_id.toString());
  }
  
  if (params.date_from) {
    queryParams.append('date_from', params.date_from);
  }
  
  if (params.date_to) {
    queryParams.append('date_to', params.date_to);
  }

  try {
    const response = await apiFetch(`/api/bills?${queryParams.toString()}`);
    
    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Brak autoryzacji');
      }
      if (response.status === 400) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Nieprawidłowe parametry zapytania');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<BillListResponse> | BillListResponse = await response.json();
    
    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
        if (!data.success) {
            throw new Error(data.message || 'Failed to fetch bills');
        }
        return data.data;
    }
    
    return data as BillListResponse;
  } catch (error) {
    console.error('Error fetching bills:', error);
    throw error;
  }
};

export const getBillDetail = async (billId: number): Promise<BillResponse> => {
  if (!billId || billId <= 0) {
    throw new Error('Nieprawidłowe ID paragonu');
  }

  try {
    const response = await apiFetch(`/api/bills/${billId}`);

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('Brak dostępu do tego paragonu');
      }
      if (response.status === 404) {
        throw new Error('Paragon nie został znaleziony');
      }
      if (response.status === 401) {
        throw new Error('Brak autoryzacji');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<BillResponse> | BillResponse = await response.json();

    if ('data' in data && 'success' in data) {
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch bill');
      }
      return data.data;
    }

    return data as BillResponse;
  } catch (error) {
    console.error('Error fetching bill detail:', error);
    throw error;
  }
};

export const getBillItems = async (
  billId: number,
  params: { skip?: number; limit?: number }
): Promise<BillItemListResponse> => {
  if (!billId || billId <= 0) {
    throw new Error('Nieprawidłowe ID paragonu');
  }

  const queryParams = new URLSearchParams();

  const limit = params.limit || 100;
  queryParams.append('limit', limit.toString());

  const skip = params.skip ?? 0;
  queryParams.append('skip', skip.toString());

  try {
    const response = await apiFetch(
      `/api/bills/${billId}/items?${queryParams.toString()}`
    );

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('Brak dostępu do tego paragonu');
      }
      if (response.status === 404) {
        throw new Error('Paragon nie został znaleziony');
      }
      if (response.status === 401) {
        throw new Error('Brak autoryzacji');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<BillItemListResponse> | BillItemListResponse =
      await response.json();

    if ('data' in data && 'success' in data) {
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch bill items');
      }
      return data.data;
    }

    return data as BillItemListResponse;
  } catch (error) {
    console.error('Error fetching bill items:', error);
    throw error;
  }
};

