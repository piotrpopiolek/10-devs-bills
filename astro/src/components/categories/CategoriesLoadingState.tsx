import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';

export const CategoriesLoadingState: React.FC = () => {
  return (
    <div className="rounded-md border p-6 space-y-4">
      {/* Simulate multiple accordion items */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-3">
          {/* Accordion header skeleton */}
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-[200px]" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-[80px]" />
              <Skeleton className="h-5 w-[80px]" />
            </div>
          </div>
          {/* Accordion content skeleton (sometimes visible) */}
          {i <= 2 && (
            <div className="pl-4 space-y-2">
              <Skeleton className="h-6 w-[180px]" />
              <Skeleton className="h-6 w-[160px]" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

