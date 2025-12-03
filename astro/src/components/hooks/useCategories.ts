import { useState, useEffect, useCallback } from 'react';
import type { CategoryResponse } from '@/types';
import { getCategories } from '@/lib/services/categories';

interface UseCategoriesReturn {
  data: CategoryResponse[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  setSkip: (skip: number) => void;
  skip: number;
  limit: number;
  refetch: () => Promise<void>;
}

export const useCategories = (initialSkip: number = 0, initialLimit: number = 100): UseCategoriesReturn => {
  const [data, setData] = useState<CategoryResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  
  const [skip, setSkip] = useState<number>(initialSkip);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getCategories({
        skip,
        limit: initialLimit,
      });
      
      // Update state with new backend structure
      setData(response.items || []);
      setTotal(response.total || 0);
      setLimit(response.limit || initialLimit);
      
    } catch (err) {
      console.error("useCategories error:", err);
      setError(err instanceof Error ? err : new Error('An unknown error occurred'));
      setData([]); 
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [skip, initialLimit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    total,
    isLoading,
    error,
    setSkip,
    skip,
    limit,
    refetch: fetchData
  };
};
