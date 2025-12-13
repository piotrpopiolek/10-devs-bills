import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { formatCurrency } from '@/lib/utils/formatting';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  label: string;
  value: number | null;
  isLoading?: boolean;
  trend?: {
    value: number; // procentowa zmiana (np. 15.5 dla +15.5%)
    isPositive: boolean; // true jeśli wzrost, false jeśli spadek
  };
  currency?: string; // domyślnie "PLN"
}

export const StatsCard: React.FC<StatsCardProps> = ({
  label,
  value,
  isLoading = false,
  trend,
  currency = 'PLN',
}) => {
  // Walidacja wartości - jeśli null, undefined lub NaN, wyświetl 0.00
  const displayValue = value === null || value === undefined || isNaN(value) ? 0 : value;
  const formattedValue = formatCurrency(displayValue, currency);

  // Jeśli jest w trakcie ładowania, wyświetl skeleton
  if (isLoading) {
    return (
      <div className="rounded-lg border bg-card p-6 shadow-sm">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-32" />
          {trend && <Skeleton className="h-4 w-20" />}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="space-y-2">
        {/* Etykieta */}
        <p className="text-sm font-medium text-muted-foreground">{label}</p>

        {/* Wartość główna */}
        <div className="flex items-baseline gap-2">
          <p className="text-2xl font-bold">{formattedValue}</p>
        </div>

        {/* Wskaźnik trendu */}
        {trend && (
          <div
            className={cn(
              'flex items-center gap-1 text-sm',
              trend.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            )}
          >
            {trend.isPositive ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span>
              {trend.isPositive ? '+' : '-'}
              {trend.value.toFixed(1)}%
            </span>
            <span className="text-muted-foreground">vs poprzedni okres</span>
          </div>
        )}
      </div>
    </div>
  );
};
