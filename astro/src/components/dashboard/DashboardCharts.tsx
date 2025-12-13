import React from 'react';
import { PieChart } from './PieChart';
import type { MonthlyReportResponse } from '@/types';
import { parseAmount } from '@/lib/utils/formatting';

interface DashboardChartsProps {
  monthlyReport: MonthlyReportResponse | null;
  isLoading: boolean;
}

export const DashboardCharts: React.FC<DashboardChartsProps> = ({
  monthlyReport,
  isLoading,
}) => {
  // Przygotuj dane dla wykresu kategorii
  const categoriesData = React.useMemo(() => {
    if (!monthlyReport?.top_categories) return [];

    return monthlyReport.top_categories.map((category) => ({
      label: category.category.name,
      value: parseAmount(category.amount),
      percentage: category.percentage,
    }));
  }, [monthlyReport]);

  // Przygotuj dane dla wykresu sklepów
  const shopsData = React.useMemo(() => {
    if (!monthlyReport?.top_shops) return [];

    return monthlyReport.top_shops.map((shop) => ({
      label: shop.shop.name,
      value: parseAmount(shop.amount),
      percentage: (parseAmount(shop.amount) / parseAmount(monthlyReport.total_amount)) * 100,
    }));
  }, [monthlyReport]);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Wykres kategorii */}
      <PieChart
        data={categoriesData}
        title="Top kategorie"
        isLoading={isLoading}
      />

      {/* Wykres sklepów */}
      <PieChart
        data={shopsData}
        title="Top sklepy"
        isLoading={isLoading}
      />
    </div>
  );
};
