import React, { useState, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { ProcessingStatus, Shop } from '@/types';
import { formatShopName } from '@/lib/utils/formatting';

interface BillsToolbarProps {
  status?: ProcessingStatus;
  shopId?: number;
  dateFrom?: string;
  dateTo?: string;
  shops?: Array<Pick<Shop, 'id' | 'name'>>;
  onStatusChange: (status: ProcessingStatus | undefined) => void;
  onShopChange: (shopId: number | undefined) => void;
  onDateRangeChange: (
    dateFrom: string | undefined,
    dateTo: string | undefined
  ) => void;
  onClearFilters?: () => void;
}

const statusOptions: Array<{ value: ProcessingStatus; label: string }> = [
  { value: 'pending', label: 'Oczekujący' },
  { value: 'processing', label: 'Przetwarzanie' },
  { value: 'completed', label: 'Zakończony' },
  { value: 'error', label: 'Błąd' },
];

export const BillsToolbar: React.FC<BillsToolbarProps> = ({
  status,
  shopId,
  dateFrom,
  dateTo,
  shops,
  onStatusChange,
  onShopChange,
  onDateRangeChange,
  onClearFilters,
}) => {
  const [localDateFrom, setLocalDateFrom] = useState<string>(dateFrom || '');
  const [localDateTo, setLocalDateTo] = useState<string>(dateTo || '');
  const [dateError, setDateError] = useState<string>('');

  // Sync local state with props
  useEffect(() => {
    setLocalDateFrom(dateFrom || '');
  }, [dateFrom]);

  useEffect(() => {
    setLocalDateTo(dateTo || '');
  }, [dateTo]);

  const validateDateRange = (from: string, to: string): boolean => {
    if (!from || !to) {
      return true; // Empty dates are valid (no filter)
    }
    
    const fromDate = new Date(from);
    const toDate = new Date(to);
    
    if (fromDate > toDate) {
      setDateError('Data początkowa nie może być późniejsza niż data końcowa');
      return false;
    }
    
    setDateError('');
    return true;
  };

  const handleDateFromChange = (value: string) => {
    setLocalDateFrom(value);
    if (validateDateRange(value, localDateTo)) {
      onDateRangeChange(value || undefined, localDateTo || undefined);
    }
  };

  const handleDateToChange = (value: string) => {
    setLocalDateTo(value);
    if (validateDateRange(localDateFrom, value)) {
      onDateRangeChange(localDateFrom || undefined, value || undefined);
    }
  };

  const hasActiveFilters = status !== undefined || shopId !== undefined || dateFrom || dateTo;

  return (
    <div className="flex flex-col gap-4 py-4">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4 w-full md:w-auto">
          <Select
            value={status || 'all'}
            onValueChange={(value) => {
              if (value === 'all') {
                onStatusChange(undefined);
              } else {
                onStatusChange(value as ProcessingStatus);
              }
            }}
          >
            <SelectTrigger className="w-full md:w-[180px]">
              <SelectValue placeholder="Wszystkie statusy" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Wszystkie statusy</SelectItem>
              {statusOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {shops && shops.length > 0 && (
            <Select
              value={shopId?.toString() || 'all'}
              onValueChange={(value) => {
                if (value === 'all') {
                  onShopChange(undefined);
                } else {
                  onShopChange(parseInt(value, 10));
                }
              }}
            >
              <SelectTrigger className="w-full md:w-[200px]">
                <SelectValue placeholder="Wszystkie sklepy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Wszystkie sklepy</SelectItem>
                {shops.map((shop) => (
                  <SelectItem key={shop.id} value={shop.id.toString()}>
                    {formatShopName(shop.name)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
            <Input
              type="date"
              placeholder="Data od"
              value={localDateFrom}
              onChange={(e) => handleDateFromChange(e.target.value)}
              className="w-full sm:w-[150px]"
            />
            <Input
              type="date"
              placeholder="Data do"
              value={localDateTo}
              onChange={(e) => handleDateToChange(e.target.value)}
              className="w-full sm:w-[150px]"
            />
          </div>
        </div>

        {hasActiveFilters && onClearFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={onClearFilters}
            className="w-full md:w-auto"
          >
            Wyczyść filtry
          </Button>
        )}
      </div>

      {dateError && (
        <div className="text-sm text-destructive">
          {dateError}
        </div>
      )}
    </div>
  );
};

