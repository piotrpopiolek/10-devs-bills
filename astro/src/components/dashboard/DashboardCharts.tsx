import React from 'react';
import { PieChart } from './PieChart';
import { LineChart } from './LineChart';
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
    if (!monthlyReport?.top_categories || !Array.isArray(monthlyReport.top_categories)) {
      return [];
    }

    return monthlyReport.top_categories
      .filter((category) => category && category.category && category.category.name)
      .map((category) => {
        // Upewnij się, że percentage jest liczbą
        let percentage = 0;
        if (typeof category.percentage === 'number' && !isNaN(category.percentage)) {
          percentage = category.percentage;
        } else if (typeof category.percentage === 'string') {
          percentage = parseFloat(category.percentage) || 0;
        }
        
        return {
          label: category.category.name,
          value: parseAmount(category.amount),
          percentage,
        };
      });
  }, [monthlyReport]);

  // Przygotuj dane dla wykresu sklepów
  const shopsData = React.useMemo(() => {
    if (!monthlyReport?.top_shops || !Array.isArray(monthlyReport.top_shops)) {
      return [];
    }

    const totalAmount = parseAmount(monthlyReport.total_amount);
    
    return monthlyReport.top_shops
      .filter((shop) => shop && shop.shop && shop.shop.name)
      .map((shop) => ({
        label: shop.shop.name,
        value: parseAmount(shop.amount),
        percentage: totalAmount > 0 
          ? (parseAmount(shop.amount) / totalAmount) * 100 
          : 0,
      }));
  }, [monthlyReport]);

  // Przygotuj dane dla wykresu liniowego (weekly breakdown)
  const weeklyData = React.useMemo(() => {
    if (!monthlyReport?.weekly_breakdown || !Array.isArray(monthlyReport.weekly_breakdown)) {
      return [];
    }

    return monthlyReport.weekly_breakdown
      .filter((week) => week && week.week_start)
      .map((week) => {
        // Formatuj datę jako krótką etykietę (np. "27.10")
        try {
          const date = new Date(week.week_start);
          if (isNaN(date.getTime())) {
            return null;
          }
          const day = date.getDate().toString().padStart(2, '0');
          const month = (date.getMonth() + 1).toString().padStart(2, '0');
          const label = `${day}.${month}`;

          return {
            label,
            value: parseAmount(week.amount),
          };
        } catch (error) {
          console.error('Error parsing week date:', week.week_start, error);
          return null;
        }
      })
      .filter((item): item is { label: string; value: number } => item !== null);
  }, [monthlyReport]);

  return (
    <div className="space-y-4">
      {/* Wykresy kołowe */}
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

      {/* Wykres liniowy - tygodniowy podział */}
      <LineChart
        data={weeklyData}
        title="Wydatki tygodniowe"
        isLoading={isLoading}
      />
    </div>
  );
};
