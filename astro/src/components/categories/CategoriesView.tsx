import React from 'react';
import { useCategories } from '@/components/hooks/useCategories';
import { CategoriesTable } from './CategoriesTable';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export const CategoriesView: React.FC = () => {
  const {
    data,
    total,
    limit,
    isLoading,
    skip,
    setSkip,
    error,
    refetch
  } = useCategories();

  // Calculate current page from skip and limit for UI display
  const currentPage = Math.floor(skip / limit) + 1;

  const handlePageChange = (newPage: number) => {
    const newSkip = (newPage - 1) * limit;
    setSkip(newSkip);
    // Optional: Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalPages = Math.ceil(total / limit);
  const showPagination = totalPages > 1;

  return (
    <div className="container mx-auto py-10 px-4 md:px-6 space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Kategorie</h1>
        <p className="text-muted-foreground">
          Zarządzaj kategoriami produktów i przeglądaj hierarchię.
        </p>
      </div>

      {error ? (
        <div className="rounded-md border border-destructive/50 p-4 text-destructive">
          <div className="flex flex-col items-center gap-2">
            <p>Wystąpił błąd podczas pobierania danych: {error.message}</p>
            <Button variant="outline" onClick={() => refetch()}>
              Spróbuj ponownie
            </Button>
          </div>
        </div>
      ) : (
        <CategoriesTable 
          data={data} 
          isLoading={isLoading} 
        />
      )}

      {showPagination && !error && (
        <div className="flex items-center justify-end space-x-2 py-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1 || isLoading}
          >
            <ChevronLeft className="h-4 w-4" />
            Poprzednia
          </Button>
          <div className="text-sm text-muted-foreground">
            Strona {currentPage} z {totalPages}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages || isLoading}
          >
            Następna
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
};

