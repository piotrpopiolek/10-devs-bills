import React from 'react';
import type { ShopResponse } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { formatShopName } from '@/lib/utils/formatting';

interface ShopsTableProps {
  data: ShopResponse[];
  isLoading: boolean;
}

export const ShopsTable: React.FC<ShopsTableProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nazwa</TableHead>
              <TableHead className="hidden md:table-cell">Adres</TableHead>
              <TableHead className="text-right">Paragony</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell><Skeleton className="h-4 w-[200px]" /></TableCell>
                <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-[300px]" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-[50px] ml-auto" /></TableCell>
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
        Nie znaleziono sklepów spełniających kryteria.
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nazwa</TableHead>
            <TableHead className="hidden md:table-cell">Adres</TableHead>
            <TableHead className="text-right">Paragony</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((shop) => (
            <TableRow key={shop.id}>
              <TableCell className="font-medium">{formatShopName(shop.name)}</TableCell>
              <TableCell className="hidden md:table-cell">
                {shop.address || "-"}
              </TableCell>
              <TableCell className="text-right">{shop.bills_count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

