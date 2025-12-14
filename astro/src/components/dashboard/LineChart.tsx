import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { formatCurrency, formatDate, parseAmount } from '@/lib/utils/formatting';

interface LineChartDataPoint {
  label: string;
  value: number;
}

interface LineChartProps {
  data: LineChartDataPoint[];
  title: string;
  isLoading?: boolean;
  className?: string;
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  title,
  isLoading = false,
  className,
}) => {
  // Oblicz wymiary wykresu
  const chartWidth = 400;
  const chartHeight = 200;
  const padding = { top: 20, right: 20, bottom: 40, left: 80 }; // Zwiększony padding.left dla wartości na osi Y
  const graphWidth = chartWidth - padding.left - padding.right;
  const graphHeight = chartHeight - padding.top - padding.bottom;

  // Oblicz wartości dla wykresu
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return null;

    const values = data.map((d) => d.value);
    const maxValue = Math.max(...values, 0);
    const minValue = Math.min(...values, 0);
    const range = maxValue - minValue || 1; // Unikaj dzielenia przez zero

    return {
      points: data.map((point, index) => {
        const x = (index / (data.length - 1 || 1)) * graphWidth + padding.left;
        const y =
          chartHeight -
          padding.bottom -
          ((point.value - minValue) / range) * graphHeight;
        return { ...point, x, y };
      }),
      maxValue,
      minValue,
    };
  }, [data, graphWidth, graphHeight, padding]);

  if (isLoading) {
    return (
      <div className={cn('rounded-lg border bg-card p-6 shadow-sm', className)}>
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>
        <div className="flex items-center justify-center">
          <div className="h-48 w-full animate-pulse rounded bg-muted" />
        </div>
      </div>
    );
  }

  if (!data || data.length === 0 || !chartData) {
    return (
      <div className={cn('rounded-lg border bg-card p-6 shadow-sm', className)}>
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>
        <div className="flex items-center justify-center">
          <p className="text-sm text-muted-foreground">Brak danych</p>
        </div>
      </div>
    );
  }

  // Utwórz path dla linii
  const pathData = chartData.points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
    .join(' ');

  // Utwórz path dla wypełnienia pod linią
  const areaPathData = [
    pathData,
    `L ${chartData.points[chartData.points.length - 1].x} ${chartHeight - padding.bottom}`,
    `L ${chartData.points[0].x} ${chartHeight - padding.bottom}`,
    'Z',
  ].join(' ');

  return (
    <div className={cn('rounded-lg border bg-card p-6 shadow-sm', className)}>
      <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>

      <div className="overflow-x-auto">
        <svg
          width={chartWidth}
          height={chartHeight}
          viewBox={`-25 0 ${chartWidth + 25} ${chartHeight}`}
          className="overflow-visible"
          style={{ marginLeft: '25px' }}
        >
          {/* Siatka pomocnicza (opcjonalnie) */}
          <defs>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="var(--chart-1)" stopOpacity="0.4" />
              <stop offset="100%" stopColor="var(--chart-1)" stopOpacity="0.1" />
            </linearGradient>
          </defs>

          {/* Wypełnienie pod linią */}
          <path
            d={areaPathData}
            fill="url(#areaGradient)"
            className="transition-opacity"
          />

          {/* Linia */}
          <path
            d={pathData}
            fill="none"
            stroke="var(--chart-1)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="transition-all"
          />

          {/* Punkty na linii */}
          {chartData.points.map((point, index) => (
            <g key={index}>
              <circle
                cx={point.x}
                cy={point.y}
                r="5"
                fill="var(--chart-1)"
                stroke="var(--background)"
                strokeWidth="2"
                className="transition-all hover:r-7"
              />
              {/* Tooltip on hover */}
              <title>
                {point.label}: {formatCurrency(point.value)}
              </title>
            </g>
          ))}

          {/* Oś Y - wartości */}
          {chartData.maxValue > 0 && (
            <g>
              {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                const value = chartData.minValue + (chartData.maxValue - chartData.minValue) * ratio;
                const y = chartHeight - padding.bottom - ratio * graphHeight;
                return (
                  <g key={ratio}>
                    <line
                      x1={padding.left - 8}
                      y1={y}
                      x2={padding.left}
                      y2={y}
                      stroke="hsl(var(--muted-foreground))"
                      strokeWidth="1"
                      opacity="0.3"
                    />
                    <text
                      x={padding.left - 10}
                      y={y + 4}
                      textAnchor="end"
                      fontSize="10"
                      fill="hsl(var(--muted-foreground))"
                    >
                      {formatCurrency(value)}
                    </text>
                  </g>
                );
              })}
            </g>
          )}

          {/* Oś X - etykiety */}
          {chartData.points.map((point, index) => {
            // Wyświetlaj co drugą etykietę, żeby nie było za dużo
            if (chartData.points.length > 5 && index % 2 !== 0) return null;

            return (
              <g key={index}>
                <line
                  x1={point.x}
                  y1={chartHeight - padding.bottom}
                  x2={point.x}
                  y2={chartHeight - padding.bottom + 5}
                  stroke="hsl(var(--muted-foreground))"
                  strokeWidth="1"
                  opacity="0.3"
                />
                <text
                  x={point.x}
                  y={chartHeight - padding.bottom + 20}
                  textAnchor="middle"
                  fontSize="10"
                  fill="hsl(var(--muted-foreground))"
                  transform={`rotate(-45 ${point.x} ${chartHeight - padding.bottom + 20})`}
                >
                  {point.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};
