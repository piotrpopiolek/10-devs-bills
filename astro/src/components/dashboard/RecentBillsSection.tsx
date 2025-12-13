import React from 'react';
import { RecentBillsList } from './RecentBillsList';
import type { BillResponse } from '@/types';

interface RecentBillsSectionProps {
  bills: BillResponse[];
  isLoading: boolean;
  error: Error | null;
  onBillClick: (billId: number) => void;
}

export const RecentBillsSection: React.FC<RecentBillsSectionProps> = ({
  bills,
  isLoading,
  error,
  onBillClick,
}) => {
  return (
    <div className="space-y-4">
      {/* Nagłówek sekcji */}
      <h2 className="text-2xl font-bold">Ostatnie paragony</h2>

      {/* Lista ostatnich paragonów */}
      <RecentBillsList
        bills={bills}
        isLoading={isLoading}
        error={error}
        onBillClick={onBillClick}
      />
    </div>
  );
};
