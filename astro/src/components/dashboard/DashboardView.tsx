import React from 'react';
import { useDashboard } from '@/components/hooks/useDashboard';
import { DashboardStats } from './DashboardStats';
import { RecentBillsSection } from './RecentBillsSection';
import { DashboardCharts } from './DashboardCharts';

export const DashboardView: React.FC = () => {
  const {
    // Daily expenses
    dailyExpenses,
    isLoadingDaily,
    dailyError,

    // Monthly expenses
    monthlyExpenses,
    previousMonthExpenses,
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
  } = useDashboard();

  // Handler dla kliknięcia w paragon
  const handleBillClick = (billId: number) => {
    if (typeof window !== 'undefined') {
      window.location.href = `/bills/${billId}`;
    }
  };

  return (
    <div className="container mx-auto space-y-6 px-4 py-10 md:px-6">
      {/* Sekcja ze statystykami */}
      <DashboardStats
        dailyExpenses={dailyExpenses}
        monthlyExpenses={monthlyExpenses}
        previousMonthExpenses={previousMonthExpenses}
        usageStats={usageStats}
        isLoadingDaily={isLoadingDaily}
        isLoadingMonthly={isLoadingMonthly}
        isLoadingUsage={isLoadingUsage}
      />

      {/* Sekcja z wykresami */}
      <DashboardCharts
        monthlyReport={monthlyReport}
        isLoading={isLoadingMonthly}
      />

      {/* Sekcja z ostatnimi paragonami */}
      <RecentBillsSection
        bills={recentBills}
        isLoading={isLoadingBills}
        error={billsError}
        onBillClick={handleBillClick}
      />
    </div>
  );
};
