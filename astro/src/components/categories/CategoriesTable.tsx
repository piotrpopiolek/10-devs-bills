import React from 'react';
import type { CategoryResponse } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

interface CategoriesTableProps {
  data: CategoryResponse[];
  isLoading: boolean;
}

export const CategoriesTable: React.FC<CategoriesTableProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nazwa</TableHead>
              <TableHead className="hidden md:table-cell">Rodzic</TableHead>
              <TableHead className="text-right">Produkty</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell><Skeleton className="h-4 w-[200px]" /></TableCell>
                <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-[150px]" /></TableCell>
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
        Nie znaleziono kategorii.
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nazwa</TableHead>
            <TableHead className="hidden md:table-cell">Rodzic</TableHead>
            <TableHead className="text-right">Produkty</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((category) => (
            <TableRow key={category.id}>
              <TableCell className="font-medium">{category.name}</TableCell>
              <TableCell className="hidden md:table-cell">
                {category.parent_id ? `ID: ${category.parent_id}` : "-"}
              </TableCell>
              <TableCell className="text-right">{category.products_count || 0}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

