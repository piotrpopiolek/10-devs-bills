import React, { useMemo } from 'react';
import type { BillItemResponse } from '@/types';
import { BillItemsTable } from './BillItemsTable';

interface BillItemsSectionProps {
  items: BillItemResponse[];
  isLoading: boolean;
  totalAmount: number | string | null;
}

export const BillItemsSection: React.FC<BillItemsSectionProps> = ({
  items,
  isLoading,
  totalAmount,
}) => {
  // Calculate sum of all items
  const itemsSum = useMemo(() => {
    if (!items || items.length === 0) {
      return 0;
    }
    return items.reduce((sum, item) => {
      const price = parseFloat(item.total_price);
      return sum + (isNaN(price) ? 0 : price);
    }, 0);
  }, [items]);

  // Format amount
  const formatAmount = (amount: number | string | null): string => {
    if (amount === null || amount === undefined) {
      return '-';
    }
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (isNaN(numAmount)) {
      return '-';
    }
    return `${numAmount.toFixed(2)} PLN`;
  };

  // Check if items sum matches bill total (with small tolerance for rounding)
  const sumMatchesTotal = useMemo(() => {
    if (totalAmount === null || totalAmount === undefined) {
      return null; // Cannot compare if total is not available
    }
    const numTotal = typeof totalAmount === 'string' ? parseFloat(totalAmount) : totalAmount;
    if (isNaN(numTotal)) {
      return null;
    }
    // Allow 0.01 PLN difference for rounding errors
    return Math.abs(itemsSum - numTotal) < 0.01;
  }, [itemsSum, totalAmount]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Pozycje paragonu ({items.length})
        </h2>
      </div>

      <BillItemsTable items={items} isLoading={isLoading} />

      {!isLoading && items.length > 0 && (
        <div className="flex flex-col items-end gap-2">
          <div className="text-right">
            <span className="text-sm text-muted-foreground">Suma pozycji: </span>
            <span className="font-medium">{formatAmount(itemsSum)}</span>
          </div>
          {totalAmount !== null && totalAmount !== undefined && (
            <>
              <div className="text-right">
                <span className="text-sm text-muted-foreground">Suma paragonu: </span>
                <span className="font-medium">{formatAmount(totalAmount)}</span>
              </div>
              {sumMatchesTotal === false && (
                <div className="text-right text-sm text-yellow-600 dark:text-yellow-400">
                  ⚠ Suma pozycji nie zgadza się z sumą paragonu
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};
