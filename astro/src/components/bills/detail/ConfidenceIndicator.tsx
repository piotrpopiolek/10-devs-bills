import React from 'react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface ConfidenceIndicatorProps {
  score: string | null;
  showTooltip?: boolean;
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  score,
  showTooltip = true,
}) => {
  // Handle null score
  if (score === null) {
    return (
      <div
        className="w-3 h-3 rounded-full bg-gray-400"
        aria-label="Pewność: brak danych"
      />
    );
  }

  // Convert string to number
  const numericScore = parseFloat(score);

  // Validate conversion
  if (isNaN(numericScore) || numericScore < 0 || numericScore > 1) {
    return (
      <div
        className="w-3 h-3 rounded-full bg-gray-400"
        aria-label="Pewność: nieprawidłowa wartość"
      />
    );
  }

  // Calculate percentage
  const percent = Math.round(numericScore * 100);

  // Determine color based on score
  let colorClass: string;
  if (numericScore >= 0.8) {
    colorClass = 'bg-green-600';
  } else if (numericScore >= 0.5) {
    colorClass = 'bg-yellow-600';
  } else {
    colorClass = 'bg-red-600';
  }

  const indicator = (
    <div
      className={cn('w-3 h-3 rounded-full', colorClass)}
      aria-label={`Pewność: ${percent}%`}
    />
  );

  if (!showTooltip) {
    return indicator;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{indicator}</TooltipTrigger>
      <TooltipContent>
        <p>Pewność: {percent}%</p>
      </TooltipContent>
    </Tooltip>
  );
};
