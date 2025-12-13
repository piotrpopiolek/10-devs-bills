import React from 'react';
import type { ProcessingStatus } from '@/types';
import { BillStatusBadge } from '../BillStatusBadge';
import { Button } from '@/components/ui/button';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BillHeaderProps {
  billId: number;
  status: ProcessingStatus;
}

export const BillHeader: React.FC<BillHeaderProps> = ({ billId, status }) => {
  const handleBreadcrumbClick = () => {
    window.location.href = '/bills';
  };

  return (
    <div className="space-y-4">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-2 text-sm text-muted-foreground">
          <li>
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-0 text-sm font-normal"
              onClick={handleBreadcrumbClick}
            >
              <Home className="h-4 w-4 mr-1" />
              Paragony
            </Button>
          </li>
          <li>
            <ChevronRight className="h-4 w-4" />
          </li>
          <li className="font-medium text-foreground">
            Paragon #{billId}
          </li>
        </ol>
      </nav>

      {/* Title and Status */}
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Paragon #{billId}</h1>
        <BillStatusBadge status={status} />
      </div>
    </div>
  );
};
