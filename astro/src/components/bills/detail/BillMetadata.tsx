import React from 'react';
import type { BillResponse } from '@/types';
import { BillStatusBadge } from '../BillStatusBadge';
import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BillMetadataProps {
  bill: BillResponse;
  onShopClick?: (shopId: number) => void;
}

export const BillMetadata: React.FC<BillMetadataProps> = ({
  bill,
  onShopClick,
}) => {
  // Format date
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  // Format amount
  const formatAmount = (amount: number | string | null): string => {
    if (amount === null || amount === undefined) {
      return 'Przetwarzanie...';
    }
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (isNaN(numAmount)) {
      return '-';
    }
    return `${numAmount.toFixed(2)} PLN`;
  };

  // Handle shop click
  const handleShopClick = (shopId: number) => {
    if (onShopClick) {
      onShopClick(shopId);
    } else {
      // Default navigation
      window.location.href = `/shops/${shopId}`;
    }
  };

  return (
    <div className="rounded-md border p-4">
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <dt className="text-sm font-medium text-muted-foreground mb-1">
            Data
          </dt>
          <dd className="text-sm font-medium">{formatDate(bill.bill_date)}</dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-muted-foreground mb-1">
            Sklep
          </dt>
          <dd>
            {bill.shop_name || bill.shop?.name ? (
              bill.shop?.id ? (
                <Button
                  variant="link"
                  className="h-auto p-0 text-sm font-medium"
                  onClick={() => handleShopClick(bill.shop!.id)}
                >
                  {bill.shop_name || bill.shop!.name}
                  <ExternalLink className="ml-1 h-3 w-3" />
                </Button>
              ) : (
                <span className="text-sm font-medium">
                  {bill.shop_name || bill.shop!.name}
                </span>
              )
            ) : (
              <span className="text-sm text-muted-foreground">
                Nieznany sklep
              </span>
            )}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-muted-foreground mb-1">
            Suma
          </dt>
          <dd className="text-sm font-medium">{formatAmount(bill.total_amount)}</dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-muted-foreground mb-1">
            Status
          </dt>
          <dd>
            <BillStatusBadge status={bill.status} />
          </dd>
        </div>
      </dl>
    </div>
  );
};
