import React from 'react';
import { useBills } from '@/components/hooks/useBills';
import { useShops } from '@/components/hooks/useShops';
import { BillsToolbar } from './BillsToolbar';
import { BillsTable } from './BillsTable';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Shop, ProcessingStatus } from '@/types';

export const BillsView: React.FC = () => {
  const {
    data,
    total,
    limit,
    isLoading,
    error,
    skip,
    status,
    shopId,
    dateFrom,
    dateTo,
    setSkip,
    setStatus,
    setShopId,
    setDateFrom,
    setDateTo,
    refetch,
  } = useBills();

  // Fetch shops for filter dropdown and for mapping shop_id to shop name
  const { data: shopsData } = useShops(0, 100);
  const shops = shopsData?.map((shop) => ({ id: shop.id, name: shop.name })) || [];
  
  // Create a map for quick shop lookup
  const shopsMap = new Map(shops.map(shop => [shop.id, shop.name]));

  const handleStatusFilterChange = (newStatus: ProcessingStatus | undefined) => {
    setStatus(newStatus);
  };

  const handleShopFilterChange = (newShopId: number | undefined) => {
    setShopId(newShopId);
  };

  const handleDateRangeChange = (
    newDateFrom: string | undefined,
    newDateTo: string | undefined
  ) => {
    setDateFrom(newDateFrom);
    setDateTo(newDateTo);
  };

  const handleClearFilters = () => {
    setStatus(undefined);
    setShopId(undefined);
    setDateFrom(undefined);
    setDateTo(undefined);
  };

  // Calculate current page from skip and limit for UI display
  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.ceil(total / limit);
  const showPagination = totalPages > 1;

  const handlePageChange = (newPage: number) => {
    const newSkip = (newPage - 1) * limit;
    setSkip(newSkip);
    // Optional: Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRowClick = (billId: number) => {
    window.location.href = `/bills/${billId}`;
  };

  const handleRetry = () => {
    refetch();
  };

  return (
    <div className="container mx-auto py-10 px-4 md:px-6 space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Lista Paragonów</h1>
        <p className="text-muted-foreground">
          Przeglądaj historię wszystkich zakupów. Filtruj paragony według statusu przetwarzania, sklepu oraz zakresu dat.
        </p>
      </div>

      <BillsToolbar
        status={status}
        shopId={shopId}
        dateFrom={dateFrom}
        dateTo={dateTo}
        shops={shops.length > 0 ? shops : undefined}
        onStatusChange={handleStatusFilterChange}
        onShopChange={handleShopFilterChange}
        onDateRangeChange={handleDateRangeChange}
        onClearFilters={handleClearFilters}
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
        <BillsTable
          data={data}
          isLoading={isLoading}
          onRowClick={handleRowClick}
          shopsMap={shopsMap}
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

