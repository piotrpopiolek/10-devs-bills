import React from 'react';
import { useShops } from '@/components/hooks/useShops';
import { ShopsToolbar } from './ShopsToolbar';
import { ShopsTable } from './ShopsTable';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export const ShopsView: React.FC = () => {
  const {
    data,
    meta,
    isLoading,
    search,
    setSearch,
    page,
    setPage,
    error,
    refetch
  } = useShops();

  const handleSearchChange = (value: string) => {
    setSearch(value);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    // Optional: Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalPages = meta ? Math.ceil(meta.total / meta.limit) : 0;
  const showPagination = meta && totalPages > 1;

  return (
    <div className="container mx-auto py-10 px-4 md:px-6 space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Sklepy</h1>
        <p className="text-muted-foreground">
          Zarządzaj listą sklepów i przeglądaj statystyki paragonów.
        </p>
      </div>

      <ShopsToolbar 
        searchTerm={search} 
        onSearchChange={handleSearchChange} 
      />

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
        <ShopsTable 
          data={data} 
          isLoading={isLoading} 
        />
      )}

      {showPagination && !error && (
        <div className="flex items-center justify-end space-x-2 py-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1 || isLoading}
          >
            <ChevronLeft className="h-4 w-4" />
            Poprzednia
          </Button>
          <div className="text-sm text-muted-foreground">
            Strona {page} z {totalPages}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= totalPages || isLoading}
          >
            Następna
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
};

