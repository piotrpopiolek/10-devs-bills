import React from 'react';
import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: 'pending' | 'approved' | 'rejected';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const statusConfig = {
    pending: {
      label: 'Oczekujący',
      variant: 'secondary' as const,
    },
    approved: {
      label: 'Zaakceptowany',
      variant: 'default' as const,
    },
    rejected: {
      label: 'Odrzucony',
      variant: 'destructive' as const,
    },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant}>
      {config.label}
    </Badge>
  );
};

