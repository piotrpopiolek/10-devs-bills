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

interface ProductCandidatesToolbarProps {
  searchTerm: string;
  status?: 'pending' | 'approved' | 'rejected';
  categoryId?: number;
  categories?: Array<Pick<Category, 'id' | 'name'>>;
  onSearchChange: (value: string) => void;
  onStatusChange: (status: 'pending' | 'approved' | 'rejected' | undefined) => void;
  onCategoryChange: (categoryId: number | undefined) => void;
}

export const ProductCandidatesToolbar: React.FC<ProductCandidatesToolbarProps> = ({
  searchTerm,
  status,
  categoryId,
  categories,
  onSearchChange,
  onStatusChange,
  onCategoryChange,
}) => {
  return (
    <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-4">
      <Input
        placeholder="Szukaj kandydatów..."
        value={searchTerm}
        onChange={(event) => onSearchChange(event.target.value)}
        className="max-w-sm w-full"
      />
      <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto">
        <Select
          value={status || 'all'}
          onValueChange={(value) => {
            if (value === 'all') {
              onStatusChange(undefined);
            } else {
              onStatusChange(value as 'pending' | 'approved' | 'rejected');
            }
          }}
        >
          <SelectTrigger className="w-full md:w-[200px]">
            <SelectValue placeholder="Wszystkie statusy" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Wszystkie statusy</SelectItem>
            <SelectItem value="pending">Oczekujący</SelectItem>
            <SelectItem value="approved">Zaakceptowany</SelectItem>
            <SelectItem value="rejected">Odrzucony</SelectItem>
          </SelectContent>
        </Select>
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
    </div>
  );
};
