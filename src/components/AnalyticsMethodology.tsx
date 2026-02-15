import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Download, FileText } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { SOURCES, getCPIHistory, getLatestCPI } from '@/lib/data'
import type { AnalyticsConfig } from '@/lib/types'

interface AnalyticsMethodologyProps {
  config: AnalyticsConfig
}

export function AnalyticsMethodology({ config }: AnalyticsMethodologyProps) {
  const cpiData = getCPIHistory(config.region)
  const latestCPI = getLatestCPI(config.region)

  const handleExportMethodologyCard = () => {
    const card = `
METHODOLOGY CARD - Wage vs Essentials Analytics
Generated: ${new Date().toISOString()}

═══════════════════════════════════════════════════════════════

ANALYSIS CONFIGURATION
─────────────────────────────────────────────────────────────
Region: ${config.region}
Time Window: ${config.dateRange.start} to ${config.dateRange.end}
Base Date: ${config.baseDate}
Wage Type: ${config.wageType === 'minimum' ? 'Minimum Wage' : 'Median Wage'}
Metric Mode: ${config.metricMode}
Verdict Threshold: ${config.verdictThreshold}
Event Window: ${config.eventWindowMonths} months

═══════════════════════════════════════════════════════════════

CORE DEFINITIONS
─────────────────────────────────────────────────────────────
Let w(t) = minimum wage ($/hour) at time t
Let p_i(t) = nominal price of item i at time t in $/unit_i
Let q_i = basket quantity/weight for item i
Let I(t) = price index (CPI) normalized so I(t0)=1 for base date t0

═══════════════════════════════════════════════════════════════

FORMULAS
─────────────────────────────────────────────────────────────

1. HOURS OF WORK (Affordability Metric)
   For single item:
     hours_i(t) = p_i(t) / w(t)
   
   For basket:
     basket_cost(t) = Σ_i p_i(t) × q_i
     basket_hours(t) = basket_cost(t) / w(t)

2. NOMINAL GROWTH RATES
   Wage growth:
     wage_growth(t1,t2) = [w(t2) / w(t1)] - 1
   
   Item price growth:
     item_growth_i(t1,t2) = [p_i(t2) / p_i(t1)] - 1
   
   Basket cost growth:
     basket_growth(t1,t2) = [basket_cost(t2) / basket_cost(t1)] - 1

3. REAL-DOLLAR ADJUSTMENTS (CPI-based)
   Real wage:
     real_wage(t) = w(t) / I(t)
   
   Real price:
     real_price_i(t) = p_i(t) / I(t)
   
   Real basket cost:
     real_basket_cost(t) = basket_cost(t) / I(t)

4. AFFORDABILITY CHANGE TEST
   Affordability ratio for item:
     affordability_ratio_i = hours_i(t2) / hours_i(t1)
   
   Affordability ratio for basket:
     basket_affordability_ratio = basket_hours(t2) / basket_hours(t1)
   
   Interpretation:
     - Ratio > 1.00: Item/basket requires MORE work hours (worse)
     - Ratio = 1.00: No change in affordability
     - Ratio < 1.00: Item/basket requires FEWER work hours (better)

5. RELATIVE OUTPACING
   For item:
     relative_outpacing_i = item_growth_i - wage_growth
   
   For basket:
     outpacing_basket = basket_growth - wage_growth
   
   Interpretation:
     - Positive: Prices grew faster than wages (affordability worsened)
     - Negative: Wages grew faster than prices (affordability improved)

6. INDEXED SERIES (Base = 100)
   Wage index:
     wage_index(t) = 100 × [w(t) / w(t0)]
   
   Price index for item:
     price_index_i(t) = 100 × [p_i(t) / p_i(t0)]
   
   Basket index:
     basket_index(t) = 100 × [basket_cost(t) / basket_cost(t0)]

═══════════════════════════════════════════════════════════════

VERDICT LOGIC
─────────────────────────────────────────────────────────────
Default rule (configurable):
  - "Kept Up": basket_affordability_ratio ≤ ${config.verdictThreshold}
  - "Lagged": basket_affordability_ratio > ${config.verdictThreshold}
  - "Unclear": Data coverage below 70%

Confidence levels based on data coverage:
  - High: ≥90% of basket items have complete data
  - Medium: 70-89% coverage
  - Low: <70% coverage

═══════════════════════════════════════════════════════════════

DATA SOURCES
─────────────────────────────────────────────────────────────
${SOURCES.map(source => `
${source.name}
Provider: ${source.provider}
License: ${source.license}
URL: ${source.url}
Retrieved: ${source.retrievalTimestamp}
`).join('\n')}

CPI Information:
Base Year: ${latestCPI?.baseYear || 1982}
Latest CPI Value: ${latestCPI?.value.toFixed(3) || 'N/A'}
Latest Date: ${latestCPI?.date || 'N/A'}
Series Length: ${cpiData.length} data points

═══════════════════════════════════════════════════════════════

BASKET COMPOSITION
─────────────────────────────────────────────────────────────
Items included: ${config.basketItemIds.length}
${config.basketItemIds.map(id => `  - ${id}`).join('\n')}

Note: This is an equal-weighted basket for demonstration purposes.
Production implementations should use statistically valid basket
weights based on household expenditure surveys.

═══════════════════════════════════════════════════════════════

LIMITATIONS & CAVEATS
─────────────────────────────────────────────────────────────
1. This analysis uses simulated data for demonstration purposes
2. Minimum wage data assumes stepwise changes with carry-forward
3. Price data may have gaps; missing values are interpolated
4. CPI adjustments use national-level index
5. Basket weights are simplified (equal weighting)
6. Regional variations may not be fully captured
7. Does not account for changes in consumption patterns
8. Event study windows are fixed and may not capture all effects

═══════════════════════════════════════════════════════════════

REPRODUCIBILITY
─────────────────────────────────────────────────────────────
All calculations are deterministic and can be reproduced using:
  - This methodology card
  - The original source data
  - The formulas specified above
  - The configuration parameters listed

═══════════════════════════════════════════════════════════════
    `.trim()

    const blob = new Blob([card], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `methodology-card-${config.region}-${config.dateRange.start}-to-${config.dateRange.end}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast.success('Methodology card downloaded')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-2xl font-bold mb-2">Methodology & Formulas</h2>
          <p className="text-muted-foreground">
            Complete documentation of calculations, data sources, and analytical approach
          </p>
        </div>
        <Button onClick={handleExportMethodologyCard} className="gap-2">
          <Download size={16} />
          Export Card
        </Button>
      </div>

      <Card className="p-6">
        <h3 className="font-display text-xl font-semibold mb-4">Core Definitions</h3>
        <div className="space-y-3 font-mono text-sm">
          <div className="p-3 bg-muted rounded">
            <strong>w(t)</strong> = minimum wage ($/hour) at time t
          </div>
          <div className="p-3 bg-muted rounded">
            <strong>p<sub>i</sub>(t)</strong> = nominal price of item i at time t in $/unit<sub>i</sub>
          </div>
          <div className="p-3 bg-muted rounded">
            <strong>q<sub>i</sub></strong> = basket quantity/weight for item i
          </div>
          <div className="p-3 bg-muted rounded">
            <strong>I(t)</strong> = price index (CPI) normalized so I(t<sub>0</sub>)=1 for base date t<sub>0</sub>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="font-display text-xl font-semibold mb-4">Key Formulas</h3>
        
        <div className="space-y-6">
          <div>
            <h4 className="font-semibold text-primary mb-3">1. Hours of Work (Affordability Metric)</h4>
            <div className="space-y-2">
              <div className="p-4 bg-muted rounded font-mono text-sm">
                <div className="mb-2">For single item:</div>
                <div className="ml-4">hours<sub>i</sub>(t) = p<sub>i</sub>(t) / w(t)</div>
              </div>
              <div className="p-4 bg-muted rounded font-mono text-sm">
                <div className="mb-2">For basket:</div>
                <div className="ml-4">basket_cost(t) = Σ<sub>i</sub> p<sub>i</sub>(t) × q<sub>i</sub></div>
                <div className="ml-4">basket_hours(t) = basket_cost(t) / w(t)</div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-primary mb-3">2. Affordability Change Test</h4>
            <div className="p-4 bg-muted rounded font-mono text-sm">
              <div>affordability_ratio = hours(t<sub>2</sub>) / hours(t<sub>1</sub>)</div>
              <div className="mt-3 text-xs text-muted-foreground not-font-mono">
                <div>• Ratio &gt; 1.00: Requires MORE work hours (worse)</div>
                <div>• Ratio = 1.00: No change</div>
                <div>• Ratio &lt; 1.00: Requires FEWER work hours (better)</div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-primary mb-3">3. Relative Outpacing</h4>
            <div className="p-4 bg-muted rounded font-mono text-sm">
              <div>relative_outpacing = price_growth - wage_growth</div>
              <div className="mt-3 text-xs text-muted-foreground">
                <div>• Positive: Prices outpaced wages</div>
                <div>• Negative: Wages outpaced prices</div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-primary mb-3">4. Real-Dollar Adjustments (CPI)</h4>
            <div className="space-y-2">
              <div className="p-4 bg-muted rounded font-mono text-sm">
                real_wage(t) = w(t) / I(t)
              </div>
              <div className="p-4 bg-muted rounded font-mono text-sm">
                real_price(t) = p(t) / I(t)
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                Using CPI base year: {latestCPI?.baseYear || 1982} = 100
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-primary mb-3">5. Indexed Series (Base = 100)</h4>
            <div className="p-4 bg-muted rounded font-mono text-sm">
              <div>wage_index(t) = 100 × [w(t) / w(t<sub>0</sub>)]</div>
              <div>basket_index(t) = 100 × [basket_cost(t) / basket_cost(t<sub>0</sub>)]</div>
              <div className="mt-3 text-xs text-muted-foreground">
                Base date (t<sub>0</sub>): {config.baseDate}
              </div>
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="font-display text-xl font-semibold mb-4">Verdict Logic</h3>
        <div className="space-y-3">
          <div className="p-4 bg-green-50 border border-green-200 rounded">
            <div className="font-semibold mb-2">✓ "Kept Up"</div>
            <div className="font-mono text-sm">basket_affordability_ratio ≤ {config.verdictThreshold}</div>
            <div className="text-sm text-muted-foreground mt-2">
              No worsening of affordability over the selected period
            </div>
          </div>
          <div className="p-4 bg-orange-50 border border-orange-200 rounded">
            <div className="font-semibold mb-2">⚠ "Lagged"</div>
            <div className="font-mono text-sm">basket_affordability_ratio &gt; {config.verdictThreshold}</div>
            <div className="text-sm text-muted-foreground mt-2">
              Basket requires more work hours than before
            </div>
          </div>
          <div className="p-4 bg-gray-50 border border-gray-200 rounded">
            <div className="font-semibold mb-2">? "Unclear"</div>
            <div className="font-mono text-sm">coverage &lt; 70%</div>
            <div className="text-sm text-muted-foreground mt-2">
              Insufficient data coverage to make determination
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="font-display text-xl font-semibold mb-4">Data Sources & Coverage</h3>
        <div className="space-y-4">
          {SOURCES.map(source => (
            <div key={source.id} className="p-4 border rounded">
              <div className="flex items-start justify-between mb-2">
                <div className="font-semibold">{source.name}</div>
                <FileText className="text-muted-foreground" size={20} />
              </div>
              <div className="text-sm space-y-1">
                <div><span className="text-muted-foreground">Provider:</span> {source.provider}</div>
                <div><span className="text-muted-foreground">License:</span> {source.license}</div>
                <div><span className="text-muted-foreground">URL:</span> <a href={source.url} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">{source.url}</a></div>
                <div className="text-xs text-muted-foreground">Retrieved: {new Date(source.retrievalTimestamp).toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="font-display text-xl font-semibold mb-4">CPI Information</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 bg-muted rounded">
            <div className="text-sm text-muted-foreground mb-1">Base Year</div>
            <div className="font-mono text-2xl font-bold">{latestCPI?.baseYear || 1982}</div>
          </div>
          <div className="p-4 bg-muted rounded">
            <div className="text-sm text-muted-foreground mb-1">Latest CPI Value</div>
            <div className="font-mono text-2xl font-bold">{latestCPI?.value.toFixed(3) || 'N/A'}</div>
          </div>
          <div className="p-4 bg-muted rounded">
            <div className="text-sm text-muted-foreground mb-1">Data Points</div>
            <div className="font-mono text-2xl font-bold">{cpiData.length}</div>
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-yellow-50 border-yellow-200">
        <h3 className="font-display text-xl font-semibold mb-4">Limitations & Caveats</h3>
        <ul className="space-y-2 text-sm">
          <li>• This analysis uses simulated data for demonstration purposes</li>
          <li>• Minimum wage data assumes stepwise changes with carry-forward</li>
          <li>• Price data may have gaps; missing values are handled via documented rules</li>
          <li>• CPI adjustments use national-level index; regional variations may differ</li>
          <li>• Basket weights are simplified (equal weighting for demonstration)</li>
          <li>• Does not account for changes in consumption patterns over time</li>
          <li>• Event study windows are fixed and may not capture all dynamic effects</li>
          <li>• No partisan messaging, blame assignment, or forecasting included</li>
        </ul>
      </Card>
    </div>
  )
}
