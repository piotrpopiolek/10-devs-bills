import { useState, useEffect, useCallback } from 'react';
import type { ProductCandidateResponse } from '@/types';
import { getProductCandidates } from '@/lib/services/product-candidates';

interface UseProductCandidatesReturn {
  data: ProductCandidateResponse[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  setSkip: (skip: number) => void;
  setSearch: (search: string) => void;
  setStatus: (status: 'pending' | 'approved' | 'rejected' | undefined) => void;
  setCategoryId: (categoryId: number | undefined) => void;
  skip: number;
  limit: number;
  search: string;
  status?: 'pending' | 'approved' | 'rejected';
  categoryId?: number;
  refetch: () => Promise<void>;
}

export const useProductCandidates = (initialSkip: number = 0, initialLimit: number = 20): UseProductCandidatesReturn => {
  const [data, setData] = useState<ProductCandidateResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  
  const [skip, setSkip] = useState<number>(initialSkip);
  const [search, setSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected' | undefined>(undefined);
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      // Reset skip only if search term actually changed
      if (search !== debouncedSearch) {
        setSkip(0);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [search, debouncedSearch]);

  // Reset skip when filters change
  useEffect(() => {
    setSkip(0);
  }, [status, categoryId]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getProductCandidates({
        skip,
        limit: initialLimit,
        search: debouncedSearch,
        status,
        category_id: categoryId
      });
      
      // Update state with new backend structure
      setData(response.items || []);
      setTotal(response.total || 0);
      setLimit(response.limit || initialLimit);
      
    } catch (err) {
      console.error("useProductCandidates error:", err);
      setError(err instanceof Error ? err : new Error('An unknown error occurred'));
      setData([]); 
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [skip, initialLimit, debouncedSearch, status, categoryId]);

  useEffect(() => {
    // Avoid fetching if search changed but not debounced yet (though the effect dependencies handle this via debounce flow)
    fetchData();
  }, [fetchData]);

  return {
    data,
    total,
    isLoading,
    error,
    setSkip,
    setSearch,
    setStatus,
    setCategoryId,
    skip,
    limit,
    search,
    status,
    categoryId,
    refetch: fetchData
  };
};

