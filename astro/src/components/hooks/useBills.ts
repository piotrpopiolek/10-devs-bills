import { useState, useEffect, useCallback } from 'react';
import type { BillResponse, ProcessingStatus } from '@/types';
import { getBills } from '@/lib/services/bills';

interface UseBillsReturn {
  data: BillResponse[];
  total: number;
  limit: number;
  isLoading: boolean;
  error: Error | null;
  skip: number;
  status?: ProcessingStatus;
  shopId?: number;
  dateFrom?: string;
  dateTo?: string;
  setSkip: (skip: number) => void;
  setStatus: (status: ProcessingStatus | undefined) => void;
  setShopId: (shopId: number | undefined) => void;
  setDateFrom: (dateFrom: string | undefined) => void;
  setDateTo: (dateTo: string | undefined) => void;
  refetch: () => Promise<void>;
}

export const useBills = (
  initialSkip: number = 0,
  initialLimit: number = 20
): UseBillsReturn => {
  const [data, setData] = useState<BillResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const [skip, setSkip] = useState<number>(initialSkip);
  const [status, setStatus] = useState<ProcessingStatus | undefined>(undefined);
  const [shopId, setShopId] = useState<number | undefined>(undefined);
  const [dateFrom, setDateFrom] = useState<string | undefined>(undefined);
  const [dateTo, setDateTo] = useState<string | undefined>(undefined);

  // Reset skip when filters change
  useEffect(() => {
    setSkip(0);
  }, [status, shopId, dateFrom, dateTo]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getBills({
        skip,
        limit: initialLimit,
        status,
        shop_id: shopId,
        date_from: dateFrom,
        date_to: dateTo,
      });

      setData(response.items || []);
      setTotal(response.total || 0);
      setLimit(response.limit || initialLimit);
    } catch (err) {
      console.error('useBills error:', err);
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred')
      );
      setData([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [skip, initialLimit, status, shopId, dateFrom, dateTo]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    total,
    limit,
    isLoading,
    error,
    skip,
    status,
    shopId,
    dateFrom,
    dateTo,
    setSkip,
    setStatus,
    setShopId,
    setDateFrom,
    setDateTo,
    refetch: fetchData,
  };
};

