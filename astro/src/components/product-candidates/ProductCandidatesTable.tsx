import React from 'react';
import type { ProductCandidateResponse } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from './StatusBadge';

interface ProductCandidatesTableProps {
  data: ProductCandidateResponse[];
  isLoading: boolean;
}

export const ProductCandidatesTable: React.FC<ProductCandidatesTableProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nazwa reprezentatywna</TableHead>
              <TableHead className="hidden md:table-cell">Status</TableHead>
              <TableHead className="hidden md:table-cell">Kategoria</TableHead>
              <TableHead className="hidden lg:table-cell">Indeks produktu</TableHead>
              <TableHead className="text-right">Potwierdzenia</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell><Skeleton className="h-4 w-[200px]" /></TableCell>
                <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-[100px]" /></TableCell>
                <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-[150px]" /></TableCell>
                <TableCell className="hidden lg:table-cell"><Skeleton className="h-4 w-[150px]" /></TableCell>
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
        Nie znaleziono kandydatów spełniających kryteria.
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nazwa reprezentatywna</TableHead>
            <TableHead className="hidden md:table-cell">Status</TableHead>
            <TableHead className="hidden md:table-cell">Kategoria</TableHead>
            <TableHead className="hidden lg:table-cell">Indeks produktu</TableHead>
            <TableHead className="text-right">Potwierdzenia</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((candidate) => (
            <TableRow key={candidate.id}>
              <TableCell className="font-medium">{candidate.representative_name}</TableCell>
              <TableCell className="hidden md:table-cell">
                <StatusBadge status={candidate.status} />
              </TableCell>
              <TableCell className="hidden md:table-cell">
                {candidate.category?.name || "-"}
              </TableCell>
              <TableCell className="hidden lg:table-cell">
                {candidate.product_index?.name || "-"}
              </TableCell>
              <TableCell className="text-right">
                {candidate.user_confirmations}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
