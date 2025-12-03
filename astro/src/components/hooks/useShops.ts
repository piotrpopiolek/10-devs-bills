import { useState, useEffect, useCallback } from 'react';
import type { ShopResponse } from '@/types';
import { getShops } from '@/lib/services/shops';

interface UseShopsReturn {
  data: ShopResponse[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  setSkip: (skip: number) => void;
  setSearch: (search: string) => void;
  skip: number;
  limit: number;
  search: string;
  refetch: () => Promise<void>;
}

export const useShops = (initialSkip: number = 0, initialLimit: number = 10): UseShopsReturn => {
  const [data, setData] = useState<ShopResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  
  const [skip, setSkip] = useState<number>(initialSkip);
  const [search, setSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');

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

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getShops({
        skip,
        limit: initialLimit,
        search: debouncedSearch
      });
      
      // Update state with new backend structure
      setData(response.items || []);
      setTotal(response.total || 0);
      setLimit(response.limit || initialLimit);
      
    } catch (err) {
      console.error("useShops error:", err);
      setError(err instanceof Error ? err : new Error('An unknown error occurred'));
      setData([]); 
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [skip, initialLimit, debouncedSearch]);

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
    skip,
    limit,
    search,
    refetch: fetchData
  };
};
