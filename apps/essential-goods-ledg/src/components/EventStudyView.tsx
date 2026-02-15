import { useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { TrendUp, TrendDown, CalendarBlank } from '@phosphor-icons/react'
import { 
  detectWageIncreaseEvents,
  getWageHistory,
  getPriceHistory,
  calculateHoursOfWork
} from '@/lib/data'
import type { AnalyticsConfig, WageIncreaseEvent } from '@/lib/types'

interface EventStudyViewProps {
  config: AnalyticsConfig
  onConfigChange: (updates: Partial<AnalyticsConfig>) => void
}

export function EventStudyView({ config, onConfigChange }: EventStudyViewProps) {
  const events = useMemo(() => {
    return detectWageIncreaseEvents(config.wageType, config.region)
      .filter(e => e.effectiveDate >= config.dateRange.start && e.effectiveDate <= config.dateRange.end)
  }, [config.wageType, config.region, config.dateRange])

  const calculateEventMetrics = (event: WageIncreaseEvent) => {
    const eventDate = new Date(event.effectiveDate)
    const preDate = new Date(eventDate)
    preDate.setMonth(preDate.getMonth() - config.eventWindowMonths)
    const postDate = new Date(eventDate)
    postDate.setMonth(postDate.getMonth() + config.eventWindowMonths)

    const wageHistory = getWageHistory(config.wageType, config.region)
    const preWage = wageHistory.find(w => w.date >= preDate.toISOString().split('T')[0])
    const postWage = wageHistory.find(w => w.date >= postDate.toISOString().split('T')[0])

    if (!preWage || !postWage) return null

    const itemMetrics = config.basketItemIds.map(itemId => {
      const priceHistory = getPriceHistory(itemId, config.region)
      const prePrice = priceHistory.find(p => p.date >= preDate.toISOString().split('T')[0])
      const postPrice = priceHistory.find(p => p.date >= postDate.toISOString().split('T')[0])

      if (!prePrice || !postPrice) return null

      const preHours = calculateHoursOfWork(prePrice.nominalPrice, preWage.wageValue)
      const postHours = calculateHoursOfWork(postPrice.nominalPrice, postWage.wageValue)
      const deltaHours = postHours - preHours

      return {
        itemId,
        preHours,
        postHours,
        deltaHours
      }
    }).filter(m => m !== null)

    const totalPreHours = itemMetrics.reduce((sum, m) => sum + m!.preHours, 0)
    const totalPostHours = itemMetrics.reduce((sum, m) => sum + m!.postHours, 0)
    const totalDeltaHours = totalPostHours - totalPreHours

    return {
      totalPreHours,
      totalPostHours,
      totalDeltaHours,
      itemMetrics
    }
  }

  if (events.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="font-display text-2xl font-bold mb-2">Wage Increase Event Studies</h2>
          <p className="text-muted-foreground">
            No wage increase events detected in the selected time period
          </p>
        </div>
        <Card className="p-12 text-center">
          <CalendarBlank size={64} className="mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">
            Try expanding your date range or selecting a different region
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-2xl font-bold mb-2">Wage Increase Event Studies</h2>
          <p className="text-muted-foreground">
            Analyzing affordability changes around minimum wage increase dates
          </p>
        </div>
        <div className="w-48">
          <Select
            value={config.eventWindowMonths.toString()}
            onValueChange={(value) => onConfigChange({ eventWindowMonths: parseInt(value) })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3">3 Month Window</SelectItem>
              <SelectItem value="6">6 Month Window</SelectItem>
              <SelectItem value="12">12 Month Window</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-4">
        {events.map((event, index) => {
          const metrics = calculateEventMetrics(event)
          
          if (!metrics) return null

          const improved = metrics.totalDeltaHours < 0
          
          return (
            <Card key={index} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-display text-xl font-bold">
                      {new Date(event.effectiveDate).toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                    </h3>
                    <Badge variant="outline" className="font-mono">
                      {event.jurisdiction}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Wage increased from ${event.oldWage.toFixed(2)} to ${event.newWage.toFixed(2)} 
                    (+{event.increasePercent.toFixed(1)}%)
                  </p>
                </div>
                <div className={`px-4 py-2 rounded-lg ${improved ? 'bg-green-50' : 'bg-orange-50'}`}>
                  <div className="text-sm text-muted-foreground mb-1">Basket Impact</div>
                  <div className={`font-mono text-2xl font-bold flex items-center gap-2 ${improved ? 'text-increase' : 'text-decrease'}`}>
                    {metrics.totalDeltaHours >= 0 ? '+' : ''}{metrics.totalDeltaHours.toFixed(2)}h
                    {improved ? (
                      <TrendDown size={24} weight="bold" />
                    ) : (
                      <TrendUp size={24} weight="bold" />
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="p-3 bg-muted rounded-lg">
                  <div className="text-xs text-muted-foreground mb-1">
                    Pre ({config.eventWindowMonths}mo before)
                  </div>
                  <div className="font-mono text-lg font-bold">
                    {metrics.totalPreHours.toFixed(2)}h
                  </div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <div className="text-xs text-muted-foreground mb-1">
                    Post ({config.eventWindowMonths}mo after)
                  </div>
                  <div className="font-mono text-lg font-bold">
                    {metrics.totalPostHours.toFixed(2)}h
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${improved ? 'bg-green-100' : 'bg-orange-100'}`}>
                  <div className="text-xs text-muted-foreground mb-1">Change</div>
                  <div className={`font-mono text-lg font-bold ${improved ? 'text-increase' : 'text-decrease'}`}>
                    {metrics.totalDeltaHours >= 0 ? '+' : ''}{metrics.totalDeltaHours.toFixed(2)}h
                  </div>
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-medium text-sm mb-3">Item-Level Changes</h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                  {metrics.itemMetrics.map((item) => {
                    if (!item) return null
                    const itemImproved = item.deltaHours < 0
                    
                    return (
                      <div key={item.itemId} className="p-2 bg-muted rounded text-sm">
                        <div className="font-medium truncate mb-1">
                          {item.itemId.split('-')[0]}
                        </div>
                        <div className={`font-mono text-xs ${itemImproved ? 'text-increase' : 'text-decrease'}`}>
                          {item.deltaHours >= 0 ? '+' : ''}{item.deltaHours.toFixed(2)}h
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {events.length > 0 && (
        <Card className="p-4 bg-muted">
          <p className="text-sm text-muted-foreground">
            <strong>Note:</strong> Event windows compare {config.eventWindowMonths} months before and after 
            each wage increase effective date. Negative Δhours indicates improved affordability 
            (basket requires fewer work hours after the wage increase).
          </p>
        </Card>
      )}
    </div>
  )
}
