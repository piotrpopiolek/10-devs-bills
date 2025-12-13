import React from 'react';
import type { BillResponse } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { BillStatusBadge } from '@/components/bills/BillStatusBadge';
import { formatCurrency, formatDate } from '@/lib/utils/formatting';
import { cn } from '@/lib/utils';

interface RecentBillsListProps {
  bills: BillResponse[];
  isLoading: boolean;
  error: Error | null;
  onBillClick: (billId: number) => void;
}

export const RecentBillsList: React.FC<RecentBillsListProps> = ({
  bills,
  isLoading,
  error,
  onBillClick,
}) => {
  // Jeśli jest błąd, wyświetl komunikat błędu
  if (error) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-sm text-destructive">
          Nie udało się pobrać ostatnich paragonów. Spróbuj ponownie.
        </p>
      </div>
    );
  }

  // Jeśli jest w trakcie ładowania, wyświetl skeleton
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Data</TableHead>
              <TableHead>Sklep</TableHead>
              <TableHead className="text-right">Kwota</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell>
                  <Skeleton className="h-4 w-[100px]" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-[150px]" />
                </TableCell>
                <TableCell className="text-right">
                  <Skeleton className="h-4 w-[80px] ml-auto" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-4 w-[100px]" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  // Jeśli lista jest pusta, wyświetl komunikat
  if (!bills || bills.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center text-muted-foreground">
        <p>Brak paragonów</p>
      </div>
    );
  }

  // Formatuj kwotę
  const formatAmount = (amount: number | string | null): string => {
    if (amount === null || amount === undefined) {
      return formatCurrency(0);
    }
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    return formatCurrency(numAmount);
  };

  // Formatuj nazwę sklepu
  const formatShopName = (bill: BillResponse): string => {
    if (bill.shop?.name) {
      return bill.shop.name;
    }
    if (bill.shop_name) {
      return bill.shop_name;
    }
    return 'Nieznany sklep';
  };

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Data</TableHead>
              <TableHead>Sklep</TableHead>
              <TableHead className="text-right">Kwota</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {bills.map((bill) => (
              <TableRow
                key={bill.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => onBillClick(bill.id)}
              >
                <TableCell className="font-medium">
                  {formatDate(bill.bill_date)}
                </TableCell>
                <TableCell>{formatShopName(bill)}</TableCell>
                <TableCell className="text-right">
                  {formatAmount(bill.total_amount)}
                </TableCell>
                <TableCell>
                  <BillStatusBadge status={bill.status} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Link "Zobacz wszystkie" */}
      <div className="flex justify-end">
        <Button
          variant="outline"
          onClick={() => {
            // Użyj window.location dla nawigacji, ponieważ Astro nie ma useNavigate w komponentach React
            if (typeof window !== 'undefined') {
              window.location.href = '/bills';
            }
          }}
        >
          Zobacz wszystkie
        </Button>
      </div>
    </div>
  );
};
