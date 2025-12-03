import React from 'react';
import { Input } from "@/components/ui/input";

interface ShopsToolbarProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
}

export const ShopsToolbar: React.FC<ShopsToolbarProps> = ({ searchTerm, onSearchChange }) => {
  return (
    <div className="flex items-center justify-between py-4">
      <Input
        placeholder="Szukaj sklepów..."
        value={searchTerm}
        onChange={(event) => onSearchChange(event.target.value)}
        className="max-w-sm"
      />
    </div>
  );
};

