import React from 'react';
import { Button } from '@/components/ui/button';

interface CategoriesErrorStateProps {
  error: Error;
  onRetry: () => void;
}

export const CategoriesErrorState: React.FC<CategoriesErrorStateProps> = ({
  error,
  onRetry,
}) => {
  return (
    <div className="rounded-md border border-destructive/50 p-4 text-destructive">
      <div className="flex flex-col items-center gap-2">
        <p className="text-center">
          Wystąpił błąd podczas pobierania danych: {error.message}
        </p>
        <Button variant="outline" onClick={onRetry}>
          Spróbuj ponownie
        </Button>
      </div>
    </div>
  );
};

