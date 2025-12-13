import React from 'react';
import type { ProductResponse } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { SynonymsList } from './SynonymsList';

interface ProductsTableProps {
  data: ProductResponse[];
  isLoading: boolean;
}

export const ProductsTable: React.FC<ProductsTableProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nazwa produktu</TableHead>
              <TableHead className="hidden md:table-cell">Kategoria</TableHead>
              <TableHead>Synonimy</TableHead>
              <TableHead className="hidden md:table-cell text-right">Liczba użyć</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell><Skeleton className="h-4 w-[200px]" /></TableCell>
                <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-[150px]" /></TableCell>
                <TableCell><Skeleton className="h-4 w-[250px]" /></TableCell>
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
        Nie znaleziono produktów spełniających kryteria.
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nazwa produktu</TableHead>
            <TableHead className="hidden md:table-cell">Kategoria</TableHead>
            <TableHead>Synonimy</TableHead>
            <TableHead className="hidden md:table-cell text-right">Liczba użyć</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((product) => (
            <TableRow key={product.id}>
              <TableCell className="font-medium">{product.name}</TableCell>
              <TableCell className="hidden md:table-cell">
                {product.category?.name || "-"}
              </TableCell>
              <TableCell>
                <SynonymsList synonyms={product.synonyms || []} maxVisible={3} />
              </TableCell>
              <TableCell className="hidden md:table-cell text-right">
                {product.usage_count || 0}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

