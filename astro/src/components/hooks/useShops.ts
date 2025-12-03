import { useState, useEffect, useCallback } from 'react';
import type { ShopResponse, PaginationMeta } from '@/types';
import { getShops } from '@/lib/services/shops';

interface UseShopsReturn {
  data: ShopResponse[];
  meta: PaginationMeta | null;
  isLoading: boolean;
  error: Error | null;
  setPage: (page: number) => void;
  setSearch: (search: string) => void;
  page: number;
  search: string;
  refetch: () => Promise<void>;
}

export const useShops = (initialPage: number = 1, initialLimit: number = 10): UseShopsReturn => {
  const [data, setData] = useState<ShopResponse[]>([]);
  const [meta, setMeta] = useState<PaginationMeta | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  
  const [page, setPage] = useState<number>(initialPage);
  const [search, setSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      if (search !== debouncedSearch) {
        setPage(1); // Reset to page 1 on new search
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [search]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getShops({
        page,
        limit: initialLimit,
        search: debouncedSearch
      });
      
      setData(response.shops);
      setMeta(response.pagination);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('An unknown error occurred'));
      setData([]); // Clear data on error or keep previous? Clearing is safer for now.
    } finally {
      setIsLoading(false);
    }
  }, [page, initialLimit, debouncedSearch]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    meta,
    isLoading,
    error,
    setPage,
    setSearch,
    page,
    search,
    refetch: fetchData
  };
};

