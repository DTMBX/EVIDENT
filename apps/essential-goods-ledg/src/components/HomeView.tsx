import { MetricCard } from '@/components/MetricCard'
import { CategoryBadge } from '@/components/CategoryBadge'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  ShoppingCart, 
  Clock, 
  TrendUp,
  Info,
  ChartLine,
  Percent,
  ArrowsClockwise
} from '@phosphor-icons/react'
import { ITEMS, getLatestPrice, calculateHoursOfWork, calculatePriceChange, getPriceHistory, getCPIHistory, calculateInflationRate, SOURCES } from '@/lib/data'
import type { UserWageConfig } from '@/lib/types'
import { useKV } from '@github/spark/hooks'
import { useState } from 'react'
import { getTimeSinceRefresh, type RefreshMetadata } from '@/lib/data-refresh'

interface HomeViewProps {
  wageConfig: UserWageConfig
  onExplore: () => void
  onCompare: (itemIds: string[]) => void
}

export function HomeView({ wageConfig, onExplore, onCompare }: HomeViewProps) {
  const [refreshMetadata] = useKV<RefreshMetadata>('data-refresh-metadata', {
    sources: {},
    lastGlobalRefresh: new Date().toISOString()
  })
  
  const basketItems = ITEMS.slice(0, 8)
  
  const totalBasketCost = basketItems.reduce((sum, item) => {
    const latest = getLatestPrice(item.id)
    return sum + (latest?.nominalPrice || 0)
  }, 0)

  const totalHoursOfWork = calculateHoursOfWork(totalBasketCost, wageConfig.hourlyWage || 15)

  const yearAgoDate = new Date()
  yearAgoDate.setFullYear(yearAgoDate.getFullYear() - 1)
  const yearAgoDateStr = yearAgoDate.toISOString().split('T')[0]

  const yearAgoBasketCost = basketItems.reduce((sum, item) => {
    const history = getPriceHistory(item.id)
    const yearAgoPoint = history.find(p => p.date >= yearAgoDateStr)
    return sum + (yearAgoPoint?.nominalPrice || 0)
  }, 0)

  const basketChange = calculatePriceChange(yearAgoBasketCost, totalBasketCost)

  const cpiHistory = getCPIHistory()
  const latestCPI = cpiHistory[cpiHistory.length - 1]
  const yearAgoCPI = cpiHistory.find(c => c.date >= yearAgoDateStr)
  const inflationRate = yearAgoCPI ? calculateInflationRate(yearAgoCPI.value, latestCPI.value) : 0

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-start justify-between gap-3 sm:gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">Essential Goods Ledger</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            Track everyday necessities through evidence-driven price and affordability data
          </p>
        </div>
        {refreshMetadata?.lastGlobalRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.hash = 'sources'}
            className="gap-1.5 sm:gap-2 text-muted-foreground hover:text-foreground text-xs sm:text-sm"
          >
            <Clock size={14} />
            <span className="text-xs hidden sm:inline">
              Updated {getTimeSinceRefresh(refreshMetadata.lastGlobalRefresh)}
            </span>
            <span className="text-xs sm:hidden">
              {getTimeSinceRefresh(refreshMetadata.lastGlobalRefresh)}
            </span>
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <MetricCard
          title="Current Basket Cost"
          value={`$${totalBasketCost.toFixed(2)}`}
          change={basketChange}
          subtitle="8 essential items"
          icon={<ShoppingCart size={24} />}
        />
        <MetricCard
          title="Hours of Work"
          value={totalHoursOfWork.toFixed(2)}
          unit="hours"
          subtitle={`@ $${wageConfig.hourlyWage?.toFixed(2)}/hr`}
          icon={<Clock size={24} />}
        />
        <MetricCard
          title="Inflation Rate (CPI)"
          value={`${inflationRate > 0 ? '+' : ''}${inflationRate.toFixed(1)}%`}
          subtitle="Past 12 months"
          icon={<Percent size={24} />}
        />
        <MetricCard
          title="Basket Change"
          value={`${basketChange > 0 ? '+' : ''}${basketChange.toFixed(1)}%`}
          subtitle="vs. general inflation"
          icon={<TrendUp size={24} />}
        />
      </div>

      <Card className="p-4 sm:p-6">
        <div className="flex items-center justify-between mb-3 sm:mb-4 gap-2 flex-wrap">
          <div>
            <h2 className="text-lg sm:text-xl font-semibold mb-0.5 sm:mb-1">Essential Basket</h2>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Curated set of everyday necessities tracked over time
            </p>
          </div>
          <Button onClick={() => onCompare(basketItems.map(i => i.id))} size="sm" className="text-xs sm:text-sm">
            <ChartLine size={16} className="mr-1.5 sm:mr-2" />
            Compare All
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {basketItems.map(item => {
            const latest = getLatestPrice(item.id)
            const history = getPriceHistory(item.id)
            const yearAgoPoint = history.find(p => p.date >= yearAgoDateStr)
            
            const change = latest && yearAgoPoint 
              ? calculatePriceChange(yearAgoPoint.nominalPrice, latest.nominalPrice)
              : 0

            const hoursOfWork = latest 
              ? calculateHoursOfWork(latest.nominalPrice, wageConfig.hourlyWage || 15)
              : 0

            return (
              <Card 
                key={item.id} 
                className="p-3 sm:p-4 hover:shadow-md transition-shadow cursor-pointer touch-manipulation"
                onClick={() => onCompare([item.id])}
              >
                <div className="space-y-2 sm:space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1 text-sm sm:text-base">{item.name}</h3>
                      <CategoryBadge category={item.category} />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-baseline gap-1.5 sm:gap-2">
                      <span className="text-xl sm:text-2xl font-bold font-mono">
                        ${latest?.nominalPrice.toFixed(2)}
                      </span>
                      <span className="text-xs sm:text-sm text-muted-foreground">
                        /{item.unitStandard}
                      </span>
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground font-mono">
                      {hoursOfWork.toFixed(2)} hours of work
                    </div>
                  </div>

                  {change !== 0 && (
                    <Badge 
                      variant="secondary"
                      className={`text-xs ${
                        change > 0 
                          ? 'bg-[var(--decrease)] text-white' 
                          : 'bg-[var(--increase)] text-white'
                      }`}
                    >
                      {change > 0 ? '+' : ''}{change.toFixed(1)}% YoY
                    </Badge>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      </Card>

      <Card className="p-4 sm:p-6 bg-muted/50 border-accent/30">
        <div className="flex items-start gap-2 sm:gap-3">
          <Info size={20} className="sm:w-6 sm:h-6 text-accent flex-shrink-0 mt-0.5 sm:mt-1" />
          <div className="space-y-1 sm:space-y-2">
            <h3 className="font-semibold text-sm sm:text-base">Evidence-First Methodology</h3>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              All prices sourced from USDA Agricultural Marketing Service and U.S. Energy Information Administration. 
              Consumer Price Index (CPI) data from Bureau of Labor Statistics (base year 1982-84 = 100). 
              Hours-of-work calculated as: price ÷ hourly wage. 
              Real prices calculated as: (nominal price ÷ CPI) × 100.
              View complete methodology and data sources in the Methodology tab.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
