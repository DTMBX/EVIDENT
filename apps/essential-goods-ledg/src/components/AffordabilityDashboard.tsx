import { useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendUp, TrendDown, MinusCircle, Info, CheckCircle, WarningCircle, XCircle } from '@phosphor-icons/react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { IndexedTrendChart } from '@/components/IndexedTrendChart'
import { 
  calculateBasketAffordabilityMetrics,
  getWageHistory,
  getPriceHistory,
  calculateIndexedSeries
} from '@/lib/data'
import type { AnalyticsConfig } from '@/lib/types'
import { ConfidenceBadge } from '@/components/ConfidenceBadge'

interface AffordabilityDashboardProps {
  config: AnalyticsConfig
}

export function AffordabilityDashboard({ config }: AffordabilityDashboardProps) {
  const metrics = useMemo(() => {
    const wageHistory = getWageHistory(config.wageType, config.region)
    
    const wageT1 = wageHistory.find(w => w.date === config.dateRange.start)
    const wageT2 = wageHistory.find(w => w.date === config.dateRange.end)
    
    if (!wageT1 || !wageT2) return null
    
    return calculateBasketAffordabilityMetrics(
      config.basketItemIds,
      config.dateRange.start,
      config.dateRange.end,
      wageT1.wageValue,
      wageT2.wageValue,
      config.region,
      config.verdictThreshold
    )
  }, [config])

  const indexedData = useMemo(() => {
    const wageHistory = getWageHistory(config.wageType, config.region)
      .filter(w => w.date >= config.dateRange.start && w.date <= config.dateRange.end)
    
    let basketCosts: Array<{ date: string; value: number }> = []
    
    wageHistory.forEach(wage => {
      let basketCost = 0
      let validItems = 0
      
      for (const itemId of config.basketItemIds) {
        const priceHistory = getPriceHistory(itemId, config.region)
        const price = priceHistory.find(p => p.date === wage.date)
        
        if (price) {
          basketCost += price.nominalPrice
          validItems++
        }
      }
      
      if (validItems > 0) {
        basketCosts.push({ date: wage.date, value: basketCost })
      }
    })
    
    const wageValues = wageHistory.map(w => w.wageValue)
    const basketValues = basketCosts.map(b => b.value)
    const dates = wageHistory.map(w => w.date)
    
    const wageIndexed = calculateIndexedSeries(wageValues, 0)
    const basketIndexed = calculateIndexedSeries(basketValues, 0)
    
    return {
      dates,
      wageIndexed,
      basketIndexed
    }
  }, [config])

  if (!metrics || !indexedData.dates.length) {
    return (
      <Card className="p-6">
        <p className="text-muted-foreground text-center">
          Insufficient data for the selected time period. Please adjust your date range.
        </p>
      </Card>
    )
  }

  const verdictConfig = {
    'kept-up': {
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      label: 'Minimum wage kept up',
      description: 'Affordability maintained or improved over this period'
    },
    'lagged': {
      icon: XCircle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      label: 'Minimum wage lagged',
      description: 'Essential goods require more work hours than before'
    },
    'unclear': {
      icon: WarningCircle,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      borderColor: 'border-gray-200',
      label: 'Unclear verdict',
      description: 'Insufficient data coverage to make determination'
    }
  }

  const verdict = verdictConfig[metrics.verdict]
  const VerdictIcon = verdict.icon

  return (
    <div className="space-y-6">
      <Card className={`p-6 border-2 ${verdict.borderColor} ${verdict.bgColor}`}>
        <div className="flex items-start gap-4">
          <VerdictIcon className={`${verdict.color} mt-1`} size={32} weight="fill" />
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="font-display text-2xl font-bold">{verdict.label}</h2>
              <ConfidenceBadge confidence={metrics.confidenceLevel} />
            </div>
            <p className="text-muted-foreground mb-4">{verdict.description}</p>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Affordability Ratio</div>
                <div className="font-mono text-xl font-bold flex items-center gap-2">
                  {metrics.affordabilityRatio.toFixed(3)}
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info size={16} className="text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs max-w-xs">
                          Ratio of hours-of-work at end vs start. 
                          &lt;1.00 = improved, &gt;1.00 = worsened
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>
              
              <div>
                <div className="text-sm text-muted-foreground mb-1">Absolute Change</div>
                <div className="font-mono text-xl font-bold flex items-center gap-2">
                  {metrics.absoluteChange >= 0 ? '+' : ''}{metrics.absoluteChange.toFixed(2)}
                  <span className="text-sm text-muted-foreground">hrs</span>
                </div>
              </div>
              
              <div>
                <div className="text-sm text-muted-foreground mb-1">Percent Change</div>
                <div className="font-mono text-xl font-bold flex items-center gap-2">
                  {metrics.percentChange >= 0 ? '+' : ''}{metrics.percentChange.toFixed(1)}%
                  {metrics.percentChange > 0 ? (
                    <TrendUp className="text-decrease" size={20} />
                  ) : metrics.percentChange < 0 ? (
                    <TrendDown className="text-increase" size={20} />
                  ) : (
                    <MinusCircle className="text-muted-foreground" size={20} />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground mb-1">Basket Cost (Start)</div>
          <div className="font-mono text-2xl font-bold">
            ${metrics.basketCostT1.toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {config.dateRange.start}
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-muted-foreground mb-1">Basket Cost (End)</div>
          <div className="font-mono text-2xl font-bold">
            ${metrics.basketCostT2.toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {config.dateRange.end}
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-muted-foreground mb-1">Nominal Growth</div>
          <div className="font-mono text-2xl font-bold flex items-center gap-2">
            {metrics.nominalGrowth >= 0 ? '+' : ''}{metrics.nominalGrowth.toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            Basket price increase
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-display text-lg font-semibold">Indexed Comparison</h3>
            <p className="text-sm text-muted-foreground">
              Both series normalized to 100 at {config.baseDate}
            </p>
          </div>
          <Badge variant="outline" className="font-mono">
            Base: {config.baseDate}
          </Badge>
        </div>
        <IndexedTrendChart
          dates={indexedData.dates}
          wageIndexed={indexedData.wageIndexed}
          basketIndexed={indexedData.basketIndexed}
          wageLabel={config.wageType === 'minimum' ? 'Minimum Wage' : 'Median Wage'}
        />
      </Card>

      <Card className="p-6">
        <div className="space-y-4">
          <h3 className="font-display text-lg font-semibold">Growth Comparison</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground mb-2">Wage Growth</div>
              <div className="font-mono text-3xl font-bold">
                {metrics.wageGrowth >= 0 ? '+' : ''}{metrics.wageGrowth.toFixed(1)}%
              </div>
            </div>
            
            <div className="p-4 bg-muted rounded-lg">
              <div className="text-sm text-muted-foreground mb-2">Price Growth</div>
              <div className="font-mono text-3xl font-bold">
                {metrics.nominalGrowth >= 0 ? '+' : ''}{metrics.nominalGrowth.toFixed(1)}%
              </div>
            </div>
          </div>

          <div className={`p-4 rounded-lg ${metrics.relativeOutpacing > 0 ? 'bg-orange-50 border border-orange-200' : 'bg-green-50 border border-green-200'}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Relative Outpacing</div>
                <div className="font-mono text-2xl font-bold">
                  {metrics.relativeOutpacing >= 0 ? '+' : ''}{metrics.relativeOutpacing.toFixed(1)}%
                </div>
              </div>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info size={20} className="text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs max-w-xs">
                      Price growth minus wage growth. Positive means prices outpaced wages.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
