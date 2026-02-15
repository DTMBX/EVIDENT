import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { 
  ChartLine, 
  TrendUp, 
  Waves, 
  Info, 
  Function,
  Eye,
  EyeSlash
} from '@phosphor-icons/react'
import { calculateVolatilityMetrics, DATA_GUARDRAILS, ECONOMIC_EVENTS } from '@/lib/generational-data'
import { getPriceHistory, getWageHistory, getCPIHistory } from '@/lib/data'

export function VolatilityExplorerView() {
  const [volatilityWindow, setVolatilityWindow] = useState<3 | 5 | 10>(5)
  const [viewMode, setViewMode] = useState<'trend' | 'raw'>('trend')
  const [showEvents, setShowEvents] = useState(true)
  const [showFormula, setShowFormula] = useState(false)
  const [showGuardrails, setShowGuardrails] = useState(true)
  const [selectedMetric, setSelectedMetric] = useState<'basket' | 'wage' | 'cpi'>('basket')

  const basketPrices = getPriceHistory('eggs-dozen')
  const basketData = basketPrices.map(p => ({ date: p.date, value: p.nominalPrice }))
  
  const wageData = getWageHistory('minimum', 'US-National').map(w => ({ 
    date: w.date, 
    value: w.wageValue 
  }))
  
  const cpiData = getCPIHistory('US-National').map(c => ({ 
    date: c.date, 
    value: c.value 
  }))

  const currentData = selectedMetric === 'basket' ? basketData : 
                      selectedMetric === 'wage' ? wageData : 
                      cpiData

  const volatilityMetrics = calculateVolatilityMetrics(
    currentData,
    volatilityWindow,
    selectedMetric === 'basket' ? 'price' : selectedMetric === 'wage' ? 'wage' : 'cpi'
  )

  const guardrails = DATA_GUARDRAILS['volatility-timeline']

  const recentEvents = ECONOMIC_EVENTS.slice(-6)

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold text-foreground mb-2">
            Stability vs Volatility Explorer
          </h1>
          <p className="text-muted-foreground max-w-3xl">
            Analyze long-term economic trends and short-term fluctuations. Compare stable growth periods with turbulent volatility cycles using transparent statistical methods.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <Label className="text-sm font-medium mb-2 block">Metric to Analyze</Label>
          <Select value={selectedMetric} onValueChange={(val: any) => setSelectedMetric(val)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="basket">Essential Basket Prices</SelectItem>
              <SelectItem value="wage">Wage Series</SelectItem>
              <SelectItem value="cpi">CPI Index</SelectItem>
            </SelectContent>
          </Select>
        </Card>

        <Card className="p-4">
          <Label className="text-sm font-medium mb-2 block">Volatility Window</Label>
          <Select 
            value={volatilityWindow.toString()} 
            onValueChange={(val) => setVolatilityWindow(parseInt(val) as 3 | 5 | 10)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3">3-Year Rolling Window</SelectItem>
              <SelectItem value="5">5-Year Rolling Window</SelectItem>
              <SelectItem value="10">10-Year Rolling Window</SelectItem>
            </SelectContent>
          </Select>
        </Card>

        <Card className="p-4">
          <Label className="text-sm font-medium mb-2 block">View Mode</Label>
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'trend' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('trend')}
              className="flex-1"
            >
              <TrendUp className="w-4 h-4 mr-1" />
              Trend
            </Button>
            <Button
              variant={viewMode === 'raw' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('raw')}
              className="flex-1"
            >
              <Waves className="w-4 h-4 mr-1" />
              Raw
            </Button>
          </div>
        </Card>

        <Card className="p-4">
          <Label className="text-sm font-medium mb-2 block">Event Overlay</Label>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {showEvents ? 'Shown' : 'Hidden'}
            </span>
            <Switch checked={showEvents} onCheckedChange={setShowEvents} />
          </div>
        </Card>
      </div>

      <Alert className="border-accent/30 bg-accent/5">
        <Info className="h-4 w-4 text-accent" />
        <AlertDescription>
          <strong>Viewing {viewMode === 'trend' ? 'Smoothed Trend' : 'Raw Data'}:</strong>{' '}
          {viewMode === 'trend' 
            ? 'This view shows a 12-month moving average to highlight long-term patterns. Raw data remains accessible via toggle.'
            : 'This view shows unsmoothed data points revealing all fluctuations. Use volatility bands to measure turbulence.'
          }
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="chart" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="chart">
            <ChartLine className="w-4 h-4 mr-2" />
            Chart View
          </TabsTrigger>
          <TabsTrigger value="metrics">
            <Function className="w-4 h-4 mr-2" />
            Metrics
          </TabsTrigger>
          <TabsTrigger value="methodology">
            <Info className="w-4 h-4 mr-2" />
            Methodology
          </TabsTrigger>
        </TabsList>

        <TabsContent value="chart" className="space-y-4">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-display text-lg font-semibold">
                {selectedMetric === 'basket' ? 'Essential Basket' : selectedMetric === 'wage' ? 'Wage' : 'CPI'} Volatility
              </h3>
              <Badge variant="outline">
                {volatilityWindow}-Year Window
              </Badge>
            </div>

            <div className="h-96 flex items-center justify-center bg-muted/20 rounded-lg border-2 border-dashed border-border">
              <div className="text-center">
                <ChartLine className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground mb-2">Interactive Volatility Chart</p>
                <p className="text-sm text-muted-foreground max-w-md">
                  Chart would display {viewMode === 'trend' ? 'smoothed trend line' : 'raw data points'} with 
                  volatility bands computed as standard deviation of annualized percent change
                  {showEvents && ' with economic event markers overlaid'}
                </p>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-chart-1 rounded-full" />
                  <span className="text-muted-foreground">{viewMode === 'trend' ? 'Trend Line' : 'Data Points'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-chart-2/30 rounded-full" />
                  <span className="text-muted-foreground">Volatility Band (±1σ)</span>
                </div>
                {showEvents && (
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-destructive rounded-full" />
                    <span className="text-muted-foreground">Economic Events</span>
                  </div>
                )}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFormula(!showFormula)}
              >
                {showFormula ? <EyeSlash className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                Formula
              </Button>
            </div>

            {showFormula && (
              <div className="mt-4 p-4 bg-muted rounded-lg font-mono text-sm">
                <div className="font-semibold mb-2">Volatility Calculation:</div>
                <div className="space-y-1 text-xs">
                  <div>volatility(t) = σ(annualized_changes[t-{volatilityWindow}y, t])</div>
                  <div className="text-muted-foreground">where annualized_change = (value[t] - value[t-1]) / value[t-1] × (12 / months_elapsed)</div>
                  <div className="text-muted-foreground">σ = standard deviation over rolling window</div>
                </div>
              </div>
            )}
          </Card>

          {showEvents && (
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-accent" />
                <h3 className="font-display font-semibold">Recent Economic Events</h3>
              </div>
              <div className="space-y-3">
                {recentEvents.map((event) => (
                  <div key={event.id} className="p-3 border rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <div className="font-medium">{event.name}</div>
                      <Badge variant="outline" className="text-xs">
                        {event.type}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground mb-2">
                      {event.date} {event.endDate && `- ${event.endDate}`}
                    </div>
                    <p className="text-sm mb-2">{event.description}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>Source: {event.source}</span>
                      <Separator orientation="vertical" className="h-3" />
                      <a 
                        href={event.citationUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-accent hover:underline"
                      >
                        View Citation
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <Card className="p-6">
            <h3 className="font-display text-lg font-semibold mb-4">Volatility Statistics</h3>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <div className="text-sm text-muted-foreground mb-1">Average Volatility</div>
                <div className="text-2xl font-mono font-bold">
                  {volatilityMetrics.length > 0
                    ? (volatilityMetrics.reduce((sum, m) => sum + m.value, 0) / volatilityMetrics.length * 100).toFixed(2)
                    : '0.00'
                  }%
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Over full period
                </div>
              </div>

              <div>
                <div className="text-sm text-muted-foreground mb-1">Peak Volatility</div>
                <div className="text-2xl font-mono font-bold text-destructive">
                  {volatilityMetrics.length > 0
                    ? (Math.max(...volatilityMetrics.map(m => m.value)) * 100).toFixed(2)
                    : '0.00'
                  }%
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Maximum observed
                </div>
              </div>

              <div>
                <div className="text-sm text-muted-foreground mb-1">Data Points</div>
                <div className="text-2xl font-mono font-bold text-accent">
                  {volatilityMetrics.length}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {volatilityWindow}-year windows analyzed
                </div>
              </div>
            </div>

            <Separator className="my-6" />

            <div>
              <h4 className="font-semibold mb-3">Interpretation Guidance</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex gap-2">
                  <span>•</span>
                  <span>Higher volatility indicates greater economic turbulence and uncertainty</span>
                </li>
                <li className="flex gap-2">
                  <span>•</span>
                  <span>Lower volatility suggests more stable, predictable economic conditions</span>
                </li>
                <li className="flex gap-2">
                  <span>•</span>
                  <span>Volatility spikes often correlate with documented shocks (oil crises, recessions)</span>
                </li>
                <li className="flex gap-2">
                  <span>•</span>
                  <span>Window length affects sensitivity: shorter windows capture rapid changes</span>
                </li>
              </ul>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="methodology" className="space-y-4">
          <Card className="p-6">
            <h3 className="font-display text-lg font-semibold mb-4">Volatility Methodology</h3>
            
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-semibold mb-2">Definition</h4>
                <p className="text-muted-foreground">
                  Volatility is measured as the standard deviation of annualized percent changes over a rolling time window. 
                  This captures the magnitude of fluctuations regardless of direction (up or down).
                </p>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">Calculation Steps</h4>
                <ol className="space-y-2 text-muted-foreground list-decimal list-inside">
                  <li>For each time period t, select data from t-window to t</li>
                  <li>Calculate percent change between consecutive periods</li>
                  <li>Annualize the percent changes (adjust for time frequency)</li>
                  <li>Compute standard deviation of annualized changes</li>
                  <li>Result is volatility metric for period t</li>
                </ol>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">Window Length Selection</h4>
                <ul className="space-y-2 text-muted-foreground">
                  <li><strong>3-Year Window:</strong> Captures short-term turbulence and rapid changes</li>
                  <li><strong>5-Year Window:</strong> Balanced view of medium-term stability patterns</li>
                  <li><strong>10-Year Window:</strong> Long-term structural volatility; smooths short shocks</li>
                </ul>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">Smoothing Methods</h4>
                <p className="text-muted-foreground mb-2">
                  When "Trend" mode is selected, data is smoothed using a 12-month moving average:
                </p>
                <div className="p-3 bg-muted rounded font-mono text-xs">
                  trend_value(t) = mean(raw_values[t-11, t])
                </div>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>

      {showGuardrails && guardrails && (
        <Card className="p-6 border-border/50 bg-muted/30">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
              <Info className="w-5 h-5 text-accent" />
              <h3 className="font-display font-semibold">What the Data Shows / What It Does Not Show</h3>
            </div>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setShowGuardrails(false)}
            >
              Hide
            </Button>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-sm mb-2 text-increase">✓ What the Data Shows</h4>
              <ul className="space-y-1.5 text-sm">
                {guardrails.whatDataShows.map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-muted-foreground">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-sm mb-2 text-decrease">✗ What It Does Not Show</h4>
              <ul className="space-y-1.5 text-sm">
                {guardrails.whatDataDoesNotShow.map((item, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-muted-foreground">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
