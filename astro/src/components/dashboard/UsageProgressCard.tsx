import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { UsageStats } from '@/types';

interface UsageProgressCardProps {
  billsThisMonth: number | null;
  monthlyLimit: number | null;
  isLoading?: boolean;
}

export const UsageProgressCard: React.FC<UsageProgressCardProps> = ({
  billsThisMonth,
  monthlyLimit,
  isLoading = false,
}) => {
  // Walidacja wartości - jeśli null, użyj domyślnych wartości
  const bills = billsThisMonth === null ? 0 : billsThisMonth;
  const limit = monthlyLimit === null ? 100 : monthlyLimit;

  // Oblicz procent użycia (maksymalnie 100%)
  const usagePercentage = limit > 0 ? Math.min(100, (bills / limit) * 100) : 0;

  // Oblicz pozostałe paragony (minimum 0)
  const remainingBills = Math.max(0, limit - bills);

  // Określ kolor paska na podstawie procentu użycia
  const getProgressColor = (percentage: number): string => {
    if (percentage >= 90) {
      return 'bg-red-500'; // Czerwony >= 90%
    }
    if (percentage >= 75) {
      return 'bg-yellow-500'; // Żółty >= 75%
    }
    return 'bg-green-500'; // Zielony < 75%
  };

  // Jeśli jest w trakcie ładowania, wyświetl skeleton
  if (isLoading) {
    return (
      <div className="rounded-lg border bg-card p-6 shadow-sm">
        <div className="space-y-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-4 w-28" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <div className="space-y-4">
        {/* Nagłówek */}
        <h3 className="text-sm font-medium text-muted-foreground">Limit paragonów</h3>

        {/* Tekst z aktualnym stanem */}
        <p className="text-lg font-semibold">
          {bills} / {limit} paragonów
        </p>

        {/* Pasek postępu */}
        <div className="space-y-2">
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-primary/20">
            <div
              className={cn('h-full w-full flex-1 transition-all', getProgressColor(usagePercentage))}
              style={{ transform: `translateX(-${100 - usagePercentage}%)` }}
            />
          </div>
        </div>

        {/* Tekst z informacją o pozostałych paragonach */}
        <p className="text-sm text-muted-foreground">
          Pozostało: {remainingBills} paragonów
        </p>
      </div>
    </div>
  );
};
