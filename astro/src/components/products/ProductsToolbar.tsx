import React from 'react';
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Category } from '@/types';

interface ProductsToolbarProps {
  searchTerm: string;
  categoryId?: number;
  categories?: Array<Pick<Category, 'id' | 'name'>>;
  onSearchChange: (value: string) => void;
  onCategoryChange: (categoryId: number | undefined) => void;
}

export const ProductsToolbar: React.FC<ProductsToolbarProps> = ({
  searchTerm,
  categoryId,
  categories,
  onSearchChange,
  onCategoryChange,
}) => {
  return (
    <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-4">
      <Input
        placeholder="Szukaj produktów..."
        value={searchTerm}
        onChange={(event) => onSearchChange(event.target.value)}
        className="max-w-sm w-full"
      />
      {categories && categories.length > 0 && (
        <Select
          value={categoryId?.toString() || 'all'}
          onValueChange={(value) => {
            if (value === 'all') {
              onCategoryChange(undefined);
            } else {
              onCategoryChange(parseInt(value, 10));
            }
          }}
        >
          <SelectTrigger className="w-full md:w-[200px]">
            <SelectValue placeholder="Wszystkie kategorie" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Wszystkie kategorie</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category.id} value={category.id.toString()}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
};

