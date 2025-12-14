import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { formatCurrency } from '@/lib/utils/formatting';

interface PieChartData {
  label: string;
  value: number;
  percentage: number;
}

interface PieChartProps {
  data: PieChartData[];
  title: string;
  isLoading?: boolean;
  className?: string;
}

// Paleta 10 kolorów dla wykresów kołowych
// Używamy zmiennych CSS dla pierwszych 5, a następnie konkretne kolory dla pozostałych 5
const CHART_COLORS = [
  'var(--chart-1)', // kolor 1 z motywu
  'var(--chart-2)', // kolor 2 z motywu
  'var(--chart-3)', // kolor 3 z motywu
  'var(--chart-4)', // kolor 4 z motywu
  'var(--chart-5)', // kolor 5 z motywu
  '#8b5cf6', // fioletowy
  '#ec4899', // różowy
  '#10b981', // zielony
  '#06b6d4', // cyjan
  '#f59e0b', // pomarańczowy
];

export const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  isLoading = false,
  className,
}) => {
  // Oblicz kąty dla każdego segmentu
  const segments = useMemo(() => {
    if (!data || data.length === 0) return [];

    const total = data.reduce((sum, item) => sum + item.value, 0);
    if (total === 0) return [];

    let currentAngle = -90; // Zaczynamy od góry (-90 stopni)

    return data.map((item, index) => {
      // Oblicz percentage na podstawie wartości - zawsze przeliczamy z wartości dla spójności
      const percentage = (item.value / total) * 100;
      
      const angle = (percentage / 100) * 360;
      const startAngle = currentAngle;
      const endAngle = currentAngle + angle;
      currentAngle = endAngle;

      // Oblicz współrzędne dla SVG path (dla koła o promieniu 80, środku w 100,100)
      const radius = 80;
      const centerX = 100;
      const centerY = 100;

      const startAngleRad = (startAngle * Math.PI) / 180;
      const endAngleRad = (endAngle * Math.PI) / 180;

      const x1 = centerX + radius * Math.cos(startAngleRad);
      const y1 = centerY + radius * Math.sin(startAngleRad);
      const x2 = centerX + radius * Math.cos(endAngleRad);
      const y2 = centerY + radius * Math.sin(endAngleRad);

      const largeArcFlag = angle > 180 ? 1 : 0;

      const pathData = [
        `M ${centerX} ${centerY}`,
        `L ${x1} ${y1}`,
        `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
        'Z',
      ].join(' ');

      return {
        ...item,
        percentage, // Użyj przeliczanego/zweryfikowanego percentage
        pathData,
        color: CHART_COLORS[index % CHART_COLORS.length],
        startAngle,
        endAngle,
      };
    });
  }, [data]);

  if (isLoading) {
    return (
      <div className={cn('rounded-lg border bg-card p-6 shadow-sm', className)}>
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>
        <div className="flex items-center justify-center">
          <div className="h-48 w-48 animate-pulse rounded-full bg-muted" />
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={cn('rounded-lg border bg-card p-6 shadow-sm', className)}>
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>
        <div className="flex items-center justify-center">
          <p className="text-sm text-muted-foreground">Brak danych</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('rounded-lg border bg-card p-6 shadow-sm', className)}>
      <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>
      
      <div className="flex flex-col items-center gap-6 md:flex-row md:items-start">
        {/* Wykres kołowy */}
        <div className="flex-shrink-0">
          <svg width="200" height="200" viewBox="0 0 200 200" className="overflow-visible">
            {segments.map((segment, index) => (
              <path
                key={index}
                d={segment.pathData}
                fill={segment.color}
                stroke="hsl(var(--background))"
                strokeWidth="2"
                className="transition-opacity hover:opacity-80"
              />
            ))}
          </svg>
        </div>

        {/* Legenda */}
        <div className="flex-1 space-y-2">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: segment.color }}
                />
                <span className="text-sm font-medium">{segment.label}</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold">
                  {formatCurrency(segment.value)}
                </div>
                <div className="text-xs text-muted-foreground">
                  {typeof segment.percentage === 'number' && !isNaN(segment.percentage)
                    ? segment.percentage.toFixed(1)
                    : '0.0'}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
