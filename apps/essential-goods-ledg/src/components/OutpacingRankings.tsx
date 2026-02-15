import { useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { TrendUp, TrendDown } from '@phosphor-icons/react'
import { CategoryBadge } from '@/components/CategoryBadge'
import { 
  calculateAffordabilityMetrics,
  getWageHistory,
  getItemById
} from '@/lib/data'
import type { AnalyticsConfig, AffordabilityMetrics } from '@/lib/types'

interface OutpacingRankingsProps {
  config: AnalyticsConfig
}

export function OutpacingRankings({ config }: OutpacingRankingsProps) {
  const rankings = useMemo(() => {
    const wageHistory = getWageHistory(config.wageType, config.region)
    
    const wageT1 = wageHistory.find(w => w.date === config.dateRange.start)
    const wageT2 = wageHistory.find(w => w.date === config.dateRange.end)
    
    if (!wageT1 || !wageT2) return []
    
    const metrics: AffordabilityMetrics[] = []
    
    for (const itemId of config.basketItemIds) {
      const metric = calculateAffordabilityMetrics(
        itemId,
        config.dateRange.start,
        config.dateRange.end,
        wageT1.wageValue,
        wageT2.wageValue,
        config.region
      )
      
      if (metric) {
        metrics.push(metric)
      }
    }
    
    return metrics.sort((a, b) => b.relativeOutpacing - a.relativeOutpacing)
  }, [config])

  if (rankings.length === 0) {
    return (
      <Card className="p-6">
        <p className="text-muted-foreground text-center">
          No data available for the selected time period.
        </p>
      </Card>
    )
  }

  const maxOutpacing = Math.max(...rankings.map(r => Math.abs(r.relativeOutpacing)))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-2xl font-bold mb-2">Item Outpacing Rankings</h2>
        <p className="text-muted-foreground">
          Essential goods ranked by how much their price growth exceeded wage growth
        </p>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]">Rank</TableHead>
              <TableHead>Item</TableHead>
              <TableHead className="text-right">Price Growth</TableHead>
              <TableHead className="text-right">Wage Growth</TableHead>
              <TableHead className="text-right">Outpacing</TableHead>
              <TableHead className="text-right">Affordability</TableHead>
              <TableHead className="w-[200px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rankings.map((item, index) => {
              const itemData = getItemById(item.itemId)
              const barWidth = (Math.abs(item.relativeOutpacing) / maxOutpacing) * 100
              const isPositive = item.relativeOutpacing > 0
              
              return (
                <TableRow key={item.itemId}>
                  <TableCell className="font-mono font-bold">
                    {index + 1}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{item.itemName}</span>
                      {itemData && <CategoryBadge category={itemData.category} />}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {item.nominalGrowth >= 0 ? '+' : ''}{item.nominalGrowth.toFixed(1)}%
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {item.wageGrowth >= 0 ? '+' : ''}{item.wageGrowth.toFixed(1)}%
                  </TableCell>
                  <TableCell className="text-right">
                    <div className={`font-mono font-bold flex items-center justify-end gap-1 ${isPositive ? 'text-decrease' : 'text-increase'}`}>
                      {item.relativeOutpacing >= 0 ? '+' : ''}{item.relativeOutpacing.toFixed(1)}%
                      {isPositive ? (
                        <TrendUp size={16} weight="bold" />
                      ) : (
                        <TrendDown size={16} weight="bold" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="font-mono text-sm">
                      <div>{item.hoursT1.toFixed(2)}h → {item.hoursT2.toFixed(2)}h</div>
                      <div className={`text-xs ${item.percentChange > 0 ? 'text-decrease' : 'text-increase'}`}>
                        {item.percentChange >= 0 ? '+' : ''}{item.percentChange.toFixed(1)}%
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="relative h-8 flex items-center">
                      <div 
                        className={`h-6 rounded ${isPositive ? 'bg-orange-200' : 'bg-green-200'}`}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h3 className="font-display font-semibold mb-3">Most Outpacing</h3>
          <div className="space-y-2">
            {rankings.slice(0, 3).map((item, index) => (
              <div key={item.itemId} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-lg font-bold text-muted-foreground">
                    {index + 1}
                  </span>
                  <span className="font-medium">{item.itemName}</span>
                </div>
                <span className="font-mono font-bold text-decrease">
                  +{item.relativeOutpacing.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="font-display font-semibold mb-3">Least Outpacing</h3>
          <div className="space-y-2">
            {rankings.slice(-3).reverse().map((item, index) => (
              <div key={item.itemId} className="flex items-center justify-between p-2 bg-green-50 rounded">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-lg font-bold text-muted-foreground">
                    {rankings.length - 2 + index}
                  </span>
                  <span className="font-medium">{item.itemName}</span>
                </div>
                <span className="font-mono font-bold text-increase">
                  {item.relativeOutpacing.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
