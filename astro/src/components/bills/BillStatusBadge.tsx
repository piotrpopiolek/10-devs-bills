import React from 'react';
import { Badge } from '@/components/ui/badge';
import type { ProcessingStatus } from '@/types';

interface BillStatusBadgeProps {
  status: ProcessingStatus;
}

const statusConfig: Record<ProcessingStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  pending: {
    label: 'Oczekujący',
    variant: 'secondary',
  },
  processing: {
    label: 'Przetwarzanie',
    variant: 'default',
  },
  to_verify: {
    label: 'Do weryfikacji',
    variant: 'outline',
  },
  completed: {
    label: 'Zakończony',
    variant: 'outline',
  },
  error: {
    label: 'Błąd',
    variant: 'destructive',
  },
};

export const BillStatusBadge: React.FC<BillStatusBadgeProps> = ({ status }) => {
  const config = statusConfig[status];
  
  // Fallback dla nieznanych statusów
  if (!config) {
    console.warn(`Unknown status: ${status}`);
    return (
      <Badge variant="outline">
        {status}
      </Badge>
    );
  }
  
  // For completed status, we need a custom green variant
  // Since Badge doesn't have a success variant by default, we'll use outline with custom styling
  if (status === 'completed') {
    return (
      <Badge variant="outline" className="border-green-500 text-green-700 dark:text-green-400">
        {config.label}
      </Badge>
    );
  }
  
  return (
    <Badge variant={config.variant}>
      {config.label}
    </Badge>
  );
};

