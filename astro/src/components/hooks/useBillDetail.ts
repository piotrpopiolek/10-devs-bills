import { useState, useEffect, useCallback } from 'react';
import type { BillResponse } from '@/types';
import { getBillDetail } from '@/lib/services/bills';

interface UseBillDetailReturn {
  bill: BillResponse | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export const useBillDetail = (billId: number): UseBillDetailReturn => {
  const [bill, setBill] = useState<BillResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!billId || billId <= 0) {
      setIsLoading(false);
      setError(new Error('Nieprawidłowe ID paragonu'));
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await getBillDetail(billId);
      setBill(response);
    } catch (err) {
      console.error('useBillDetail error:', err);
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred')
      );
      setBill(null);
    } finally {
      setIsLoading(false);
    }
  }, [billId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    bill,
    isLoading,
    error,
    refetch: fetchData,
  };
};

