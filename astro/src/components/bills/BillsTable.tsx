import React from 'react';
import type { BillResponse } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { BillStatusBadge } from './BillStatusBadge';
import { formatShopName } from '@/lib/utils/formatting';

interface BillsTableProps {
  data: BillResponse[];
  isLoading: boolean;
  onRowClick?: (billId: number) => void;
  shopsMap?: Map<number, string>;
}

export const BillsTable: React.FC<BillsTableProps> = ({ 
  data, 
  isLoading,
  onRowClick,
  shopsMap = new Map()
}) => {
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
              <TableHead className="hidden md:table-cell text-right">Liczba pozycji</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell><Skeleton className="h-4 w-[120px]" /></TableCell>
                <TableCell><Skeleton className="h-4 w-[150px]" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-[80px] ml-auto" /></TableCell>
                <TableCell><Skeleton className="h-4 w-[100px]" /></TableCell>
                <TableCell className="hidden md:table-cell text-right"><Skeleton className="h-4 w-[50px] ml-auto" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center text-muted-foreground">
        Nie znaleziono paragonów spełniających kryteria.
      </div>
    );
  }

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const formatAmount = (amount: number | string | null): string => {
    if (amount === null || amount === undefined) {
      return '-';
    }
    // Handle both string and number types
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (isNaN(numAmount)) {
      return '-';
    }
    return `${numAmount.toFixed(2)} zł`;
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Sklep</TableHead>
            <TableHead className="text-right">Kwota</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="hidden md:table-cell text-right">Liczba pozycji</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((bill) => {
            // Get shop name from shopsMap if shop_id is available, otherwise use shop object
            const rawShopName = bill.shop?.name || 
              (bill.shop_id && shopsMap.get(bill.shop_id)) || 
              null;
            const shopName = formatShopName(rawShopName);
            
            return (
              <TableRow 
                key={bill.id}
                onClick={() => onRowClick?.(bill.id)}
                className={onRowClick ? "cursor-pointer hover:bg-muted/50" : ""}
              >
                <TableCell>{formatDate(bill.bill_date)}</TableCell>
                <TableCell>{shopName}</TableCell>
                <TableCell className="text-right">{formatAmount(bill.total_amount)}</TableCell>
                <TableCell>
                  <BillStatusBadge status={bill.status} />
                </TableCell>
                <TableCell className="hidden md:table-cell text-right">
                  {bill.items_count ?? '-'}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};

