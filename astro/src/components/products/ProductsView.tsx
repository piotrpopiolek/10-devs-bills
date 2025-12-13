import React, { useEffect, useState } from 'react';
import { useProducts } from '@/components/hooks/useProducts';
import { useCategories } from '@/components/hooks/useCategories';
import { ProductsToolbar } from './ProductsToolbar';
import { ProductsTable } from './ProductsTable';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Category } from '@/types';

export const ProductsView: React.FC = () => {
  const {
    data,
    total,
    limit,
    isLoading,
    search,
    setSearch,
    categoryId,
    setCategoryId,
    skip,
    setSkip,
    error,
    refetch
  } = useProducts();

  // Fetch categories for filter dropdown
  const { data: categoriesData } = useCategories(0, 100);
  const [categories, setCategories] = useState<Array<Pick<Category, 'id' | 'name'>>>([]);

  useEffect(() => {
    if (categoriesData && categoriesData.length > 0) {
      // Flatten categories (including children) for the filter dropdown
      const flattenCategories = (cats: typeof categoriesData): Array<Pick<Category, 'id' | 'name'>> => {
        const result: Array<Pick<Category, 'id' | 'name'>> = [];
        const processCategory = (cat: typeof categoriesData[0]) => {
          result.push({ id: cat.id, name: cat.name });
          if (cat.children && cat.children.length > 0) {
            cat.children.forEach(processCategory);
          }
        };
        cats.forEach(processCategory);
        return result;
      };
      setCategories(flattenCategories(categoriesData));
    }
  }, [categoriesData]);

  const handleSearchChange = (value: string) => {
    setSearch(value);
  };

  const handleCategoryFilterChange = (newCategoryId: number | undefined) => {
    setCategoryId(newCategoryId);
  };

  // Calculate current page from skip and limit for UI display
  const currentPage = Math.floor(skip / limit) + 1;

  const handlePageChange = (newPage: number) => {
    const newSkip = (newPage - 1) * limit;
    setSkip(newSkip);
    // Optional: Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRetry = () => {
    refetch();
  };

  const totalPages = Math.ceil(total / limit);
  const showPagination = totalPages > 1;

  return (
    <div className="container mx-auto py-10 px-4 md:px-6 space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Katalog Produktów</h1>
        <p className="text-muted-foreground">
          Przeglądaj bazę wiedzy o produktach i ich kategoryzacji. Znormalizowane nazwy produktów, przypisane kategorie oraz synonimy (warianty nazw odczytane przez OCR).
        </p>
      </div>

      <ProductsToolbar
        searchTerm={search}
        categoryId={categoryId}
        categories={categories.length > 0 ? categories : undefined}
        onSearchChange={handleSearchChange}
        onCategoryChange={handleCategoryFilterChange}
      />

      {error ? (
        <div className="rounded-md border border-destructive/50 p-4 text-destructive">
          <div className="flex flex-col items-center gap-2">
            <p>Wystąpił błąd podczas pobierania danych: {error.message}</p>
            <Button variant="outline" onClick={handleRetry}>
              Spróbuj ponownie
            </Button>
          </div>
        </div>
      ) : (
        <ProductsTable
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

