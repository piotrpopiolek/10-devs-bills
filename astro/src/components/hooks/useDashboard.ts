import { useState, useEffect, useCallback } from 'react';
import type {
  UsageStats,
  BillResponse,
  MonthlyReportResponse,
} from '@/types';
import { getDailyReport, getMonthlyReport } from '@/lib/services/reports';
import { authService } from '@/lib/services/auth';
import { getBills } from '@/lib/services/bills';
import { getCurrentMonth, getPreviousMonth, parseAmount } from '@/lib/utils/formatting';

interface UseDashboardReturn {
  // Daily expenses (z GET /api/v1/reports/daily)
  dailyExpenses: number | null;
  isLoadingDaily: boolean;
  dailyError: Error | null;

  // Monthly expenses (z GET /api/v1/reports/monthly)
  monthlyExpenses: number | null;
  previousMonthExpenses: number | null;
  monthlyReport: MonthlyReportResponse | null;
  isLoadingMonthly: boolean;
  monthlyError: Error | null;

  // Usage stats (z GET /api/v1/users/me)
  usageStats: UsageStats | null;
  isLoadingUsage: boolean;
  usageError: Error | null;

  // Recent bills (z GET /api/v1/bills)
  recentBills: BillResponse[];
  isLoadingBills: boolean;
  billsError: Error | null;

  // Refetch functions
  refetchAll: () => Promise<void>;
  refetchDaily: () => Promise<void>;
  refetchMonthly: () => Promise<void>;
  refetchUsage: () => Promise<void>;
  refetchBills: () => Promise<void>;
}

export const useDashboard = (): UseDashboardReturn => {
  // Daily expenses state
  const [dailyExpenses, setDailyExpenses] = useState<number | null>(null);
  const [isLoadingDaily, setIsLoadingDaily] = useState<boolean>(true);
  const [dailyError, setDailyError] = useState<Error | null>(null);

  // Monthly expenses state
  const [monthlyExpenses, setMonthlyExpenses] = useState<number | null>(null);
  const [previousMonthExpenses, setPreviousMonthExpenses] = useState<number | null>(null);
  const [monthlyReport, setMonthlyReport] = useState<MonthlyReportResponse | null>(null);
  const [isLoadingMonthly, setIsLoadingMonthly] = useState<boolean>(true);
  const [monthlyError, setMonthlyError] = useState<Error | null>(null);

  // Usage stats state
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [isLoadingUsage, setIsLoadingUsage] = useState<boolean>(true);
  const [usageError, setUsageError] = useState<Error | null>(null);

  // Recent bills state
  const [recentBills, setRecentBills] = useState<BillResponse[]>([]);
  const [isLoadingBills, setIsLoadingBills] = useState<boolean>(true);
  const [billsError, setBillsError] = useState<Error | null>(null);

  // Helper function to convert amount to number (handles string/number)
  // Moved outside callbacks to avoid dependency issues
  const parseAmount = useCallback((amount: number | string | null | undefined): number => {
    if (amount === null || amount === undefined) return 0;
    if (typeof amount === 'string') {
      const parsed = parseFloat(amount);
      return isNaN(parsed) ? 0 : parsed;
    }
    return amount;
  }, []);

  // Fetch daily expenses
  const fetchDaily = useCallback(async () => {
    setIsLoadingDaily(true);
    setDailyError(null);
    try {
      const report = await getDailyReport();
      setDailyExpenses(parseAmount(report.total_amount));
    } catch (err) {
      console.error('Error fetching daily expenses:', err);
      setDailyError(
        err instanceof Error ? err : new Error('Failed to fetch daily expenses')
      );
      setDailyExpenses(null);
    } finally {
      setIsLoadingDaily(false);
    }
  }, []);

  // Fetch monthly expenses (current and previous month)
  const fetchMonthly = useCallback(async () => {
    setIsLoadingMonthly(true);
    setMonthlyError(null);
    try {
      const currentMonth = getCurrentMonth();
      const previousMonth = getPreviousMonth(currentMonth);

      // Fetch both months in parallel, but handle errors gracefully
      const [currentReport, previousReport] = await Promise.allSettled([
        getMonthlyReport(currentMonth),
        getMonthlyReport(previousMonth).catch(() => null), // Ignore errors for previous month
      ]);

      // Handle current month result
      if (currentReport.status === 'fulfilled') {
        const report = currentReport.value;
        console.log('Monthly report received:', {
          total_amount: report.total_amount,
          top_categories: report.top_categories?.length || 0,
          top_shops: report.top_shops?.length || 0,
          weekly_breakdown: report.weekly_breakdown?.length || 0,
        });
        setMonthlyExpenses(parseAmount(report.total_amount));
        setMonthlyReport(report); // Zapisz pełny raport dla komponentów wykresów
      } else {
        console.error('Error fetching current month report:', currentReport.reason);
        throw currentReport.reason;
      }

      // Handle previous month result (optional, don't throw if it fails)
      if (previousReport.status === 'fulfilled' && previousReport.value) {
        setPreviousMonthExpenses(parseAmount(previousReport.value.total_amount));
      } else {
        setPreviousMonthExpenses(0); // Default to 0 if previous month fetch fails
      }
    } catch (err) {
      console.error('Error fetching monthly expenses:', err);
      setMonthlyError(
        err instanceof Error ? err : new Error('Failed to fetch monthly expenses')
      );
      setMonthlyExpenses(null);
      setPreviousMonthExpenses(null);
      setMonthlyReport(null); // Wyczyść raport w przypadku błędu
    } finally {
      setIsLoadingMonthly(false);
    }
  }, []);

  // Fetch usage stats
  const fetchUsage = useCallback(async () => {
    setIsLoadingUsage(true);
    setUsageError(null);
    try {
      const profile = await authService.getUserProfile();
      setUsageStats(profile.usage);
    } catch (err) {
      console.error('Error fetching usage stats:', err);
      setUsageError(
        err instanceof Error ? err : new Error('Failed to fetch usage stats')
      );
      setUsageStats(null);
    } finally {
      setIsLoadingUsage(false);
    }
  }, []);

  // Fetch recent bills
  const fetchBills = useCallback(async () => {
    setIsLoadingBills(true);
    setBillsError(null);
    try {
      const response = await getBills({ limit: 5, skip: 0 });
      setRecentBills(response.items || []);
    } catch (err) {
      console.error('Error fetching recent bills:', err);
      setBillsError(
        err instanceof Error ? err : new Error('Failed to fetch recent bills')
      );
      setRecentBills([]);
    } finally {
      setIsLoadingBills(false);
    }
  }, []);

  // Fetch all data on mount
  useEffect(() => {
    // Fetch all data in parallel
    fetchDaily();
    fetchMonthly();
    fetchUsage();
    fetchBills();
  }, [fetchDaily, fetchMonthly, fetchUsage, fetchBills]);

  // Refetch all
  const refetchAll = useCallback(async () => {
    await Promise.all([
      fetchDaily(),
      fetchMonthly(),
      fetchUsage(),
      fetchBills(),
    ]);
  }, [fetchDaily, fetchMonthly, fetchUsage, fetchBills]);

  // Auto-refresh dashboard data every 2 minutes (120 seconds)
  useEffect(() => {
    const intervalId = setInterval(() => {
      console.log('Auto-refreshing dashboard data...');
      refetchAll();
    }, 2 * 60 * 1000); // 2 minutes in milliseconds

    // Cleanup interval on unmount
    return () => {
      clearInterval(intervalId);
    };
  }, [refetchAll]);

  return {
    // Daily expenses
    dailyExpenses,
    isLoadingDaily,
    dailyError,

    // Monthly expenses
    monthlyExpenses,
    previousMonthExpenses,
    monthlyReport,
    isLoadingMonthly,
    monthlyError,

    // Usage stats
    usageStats,
    isLoadingUsage,
    usageError,

    // Recent bills
    recentBills,
    isLoadingBills,
    billsError,

    // Refetch functions
    refetchAll,
    refetchDaily: fetchDaily,
    refetchMonthly: fetchMonthly,
    refetchUsage: fetchUsage,
    refetchBills: fetchBills,
  };
};
