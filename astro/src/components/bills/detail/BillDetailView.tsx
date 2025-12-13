import React, { useEffect } from 'react';
import { useBillDetail } from '@/components/hooks/useBillDetail';
import { useBillItems } from '@/components/hooks/useBillItems';
import { BillHeader } from './BillHeader';
import { BillMetadata } from './BillMetadata';
import { BillImageViewer } from './BillImageViewer';
import { BillItemsSection } from './BillItemsSection';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface BillDetailViewProps {
  billId: number;
}

export const BillDetailView: React.FC<BillDetailViewProps> = ({ billId }) => {
  const {
    bill,
    isLoading: isBillLoading,
    error: billError,
    refetch: refetchBill,
  } = useBillDetail(billId);

  const {
    items,
    isLoading: isItemsLoading,
    error: itemsError,
    refetch: refetchItems,
  } = useBillItems(billId);

  // Polling statusu paragonu, gdy status === "processing"
  useEffect(() => {
    if (!bill || bill.status !== 'processing') {
      return;
    }

    const intervalId = setInterval(() => {
      refetchBill();
    }, 5000); // Polling co 5 sekund

    return () => {
      clearInterval(intervalId);
    };
  }, [bill?.status, refetchBill]);

  // Handle shop click navigation
  const handleShopClick = (shopId: number) => {
    window.location.href = `/shops/${shopId}`;
  };

  // Handle retry
  const handleRetry = async () => {
    await Promise.all([refetchBill(), refetchItems()]);
  };

  // Handle image refresh
  const handleImageRefresh = async () => {
    await refetchBill();
  };

  // Validation: check if billId is valid
  if (!billId || billId <= 0) {
    return (
      <div className="container mx-auto py-10 px-4 md:px-6">
        <div className="rounded-md border border-destructive p-8 text-center">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-destructive" />
          <p className="text-destructive font-medium">
            Nieprawidłowe ID paragonu
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (billError) {
    return (
      <div className="container mx-auto py-10 px-4 md:px-6">
        <div className="rounded-md border border-destructive p-8 text-center space-y-4">
          <AlertCircle className="h-12 w-12 mx-auto text-destructive" />
          <div>
            <p className="text-destructive font-medium mb-2">
              {billError.message || 'Wystąpił błąd podczas pobierania danych paragonu'}
            </p>
            <Button onClick={handleRetry} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Spróbuj ponownie
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Loading state (initial load)
  if (isBillLoading && !bill) {
    return (
      <div className="container mx-auto py-10 px-4 md:px-6 space-y-6">
        <div className="h-8 bg-muted animate-pulse rounded" />
        <div className="h-32 bg-muted animate-pulse rounded" />
        <div className="h-96 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  // No bill data
  if (!bill) {
    return (
      <div className="container mx-auto py-10 px-4 md:px-6">
        <div className="rounded-md border p-8 text-center text-muted-foreground">
          <p>Nie znaleziono paragonu</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-10 px-4 md:px-6 space-y-6">
      <BillHeader billId={bill.id} status={bill.status} />

      <BillMetadata bill={bill} onShopClick={handleShopClick} />

      {itemsError && (
        <div className="rounded-md border border-destructive p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              <p className="text-sm text-destructive">
                {itemsError.message || 'Wystąpił błąd podczas pobierania pozycji'}
              </p>
            </div>
            <Button onClick={refetchItems} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Spróbuj ponownie
            </Button>
          </div>
        </div>
      )}

      <BillItemsSection
        items={items}
        isLoading={isItemsLoading}
        totalAmount={bill.total_amount}
      />

      <BillImageViewer
        imageUrl={bill.image_signed_url || null}
        imageExpiresAt={bill.image_expires_at || null}
        isLoading={isBillLoading}
        onRefresh={handleImageRefresh}
      />
    </div>
  );
};
