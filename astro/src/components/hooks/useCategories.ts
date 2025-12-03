import { useState, useEffect, useCallback } from 'react';
import type { CategoryResponse, PaginationMeta } from '@/types';
import { getCategories } from '@/lib/services/categories';

interface UseCategoriesReturn {
  data: CategoryResponse[];
  meta: PaginationMeta | null;
  isLoading: boolean;
  error: Error | null;
  setSkip: (skip: number) => void;
  skip: number;
  refetch: () => Promise<void>;
}

export const useCategories = (initialSkip: number = 0, initialLimit: number = 100): UseCategoriesReturn => {
  const [data, setData] = useState<CategoryResponse[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
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
      
      // Safe access to data
      const categoriesData = response.categories || []; 
      setData(categoriesData);
      setMeta(response.pagination || null);
    } catch (err) {
      console.error("useCategories error:", err);
      setError(err instanceof Error ? err : new Error('An unknown error occurred'));
      setData([]); 
    } finally {
      setIsLoading(false);
    }
  }, [skip, initialLimit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    meta,
    isLoading,
    error,
    setSkip,
    skip,
    refetch: fetchData
  };
};

