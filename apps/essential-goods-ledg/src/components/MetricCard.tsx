import { Card } from '@/components/ui/card'
import { TrendUp, TrendDown } from '@phosphor-icons/react'
import type { ReactNode } from 'react'

interface MetricCardProps {
  title: string
  value: string | number
  unit?: string
  change?: number
  subtitle?: string
  icon?: ReactNode
  footer?: ReactNode
  onClick?: () => void
}

export function MetricCard({
  title,
  value,
  unit,
  change,
  subtitle,
  icon,
  footer,
  onClick
}: MetricCardProps) {
  const isIncrease = change !== undefined && change > 0
  const isDecrease = change !== undefined && change < 0

  return (
    <Card
      className={`p-3 sm:p-4 transition-all duration-200 hover:shadow-md ${
        onClick ? 'cursor-pointer touch-manipulation' : ''
      }`}
      onClick={onClick}
    >
      <div className="space-y-2 sm:space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-0.5 sm:space-y-1 flex-1 min-w-0">
            <p className="text-xs sm:text-sm font-medium text-muted-foreground">{title}</p>
            <div className="flex items-baseline gap-1.5 sm:gap-2 flex-wrap">
              <span className="text-xl sm:text-2xl font-bold font-mono leading-none">{value}</span>
              {unit && (
                <span className="text-xs sm:text-sm text-muted-foreground font-mono">
                  {unit}
                </span>
              )}
            </div>
          </div>
          {icon && <div className="text-muted-foreground flex-shrink-0">{icon}</div>}
        </div>

        {(change !== undefined || subtitle) && (
          <div className="flex items-center justify-between text-xs sm:text-sm gap-2">
            {subtitle && <span className="text-muted-foreground truncate">{subtitle}</span>}
            {change !== undefined && (
              <div
                className={`flex items-center gap-1 font-medium flex-shrink-0 ${
                  isIncrease
                    ? 'text-[var(--increase)]'
                    : isDecrease
                    ? 'text-[var(--decrease)]'
                    : 'text-muted-foreground'
                }`}
              >
                {isIncrease && <TrendUp size={14} weight="bold" />}
                {isDecrease && <TrendDown size={14} weight="bold" />}
                <span>{Math.abs(change).toFixed(1)}%</span>
              </div>
            )}
          </div>
        )}

        {footer && <div className="pt-2 border-t">{footer}</div>}
      </div>
    </Card>
  )
}
