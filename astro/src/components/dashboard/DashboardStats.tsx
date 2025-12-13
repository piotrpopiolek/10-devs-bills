import React from 'react';
import { StatsCard } from './StatsCard';
import { UsageProgressCard } from './UsageProgressCard';
import { calculateTrend } from '@/lib/utils/formatting';
import type { UsageStats } from '@/types';

interface DashboardStatsProps {
  dailyExpenses: number | null;
  monthlyExpenses: number | null;
  previousMonthExpenses: number | null;
  usageStats: UsageStats | null;
  isLoadingDaily: boolean;
  isLoadingMonthly: boolean;
  isLoadingUsage: boolean;
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({
  dailyExpenses,
  monthlyExpenses,
  previousMonthExpenses,
  usageStats,
  isLoadingDaily,
  isLoadingMonthly,
  isLoadingUsage,
}) => {
  // Oblicz trend dla wydatków miesięcznych
  const monthlyTrend =
    monthlyExpenses !== null &&
    previousMonthExpenses !== null &&
    previousMonthExpenses > 0
      ? calculateTrend(monthlyExpenses, previousMonthExpenses)
      : undefined;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {/* Wydatki dzisiaj */}
      <StatsCard
        label="Wydatki dzisiaj"
        value={dailyExpenses}
        isLoading={isLoadingDaily}
      />

      {/* Wydatki w tym miesiącu */}
      <StatsCard
        label="Wydatki w tym miesiącu"
        value={monthlyExpenses}
        isLoading={isLoadingMonthly}
        trend={monthlyTrend}
      />

      {/* Limit paragonów */}
      <UsageProgressCard
        billsThisMonth={usageStats?.bills_this_month ?? null}
        monthlyLimit={usageStats?.monthly_limit ?? null}
        isLoading={isLoadingUsage}
      />
    </div>
  );
};
