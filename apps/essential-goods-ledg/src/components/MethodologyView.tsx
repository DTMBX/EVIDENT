import { Card } from '@/components/ui/card'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { SOURCES } from '@/lib/data'
import { Clock, Link as LinkIcon } from '@phosphor-icons/react'

export function MethodologyView() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Methodology & Sources</h1>
        <p className="text-muted-foreground">
          Transparent formulas, data provenance, and known limitations
        </p>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Core Metrics</h2>
        
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="nominal">
            <AccordionTrigger>Nominal Price</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3">
                <div className="bg-muted p-3 rounded font-mono text-sm">
                  nominal_price = price_in_current_dollars
                </div>
                <p className="text-sm text-muted-foreground">
                  The actual dollar amount at a given point in time, unadjusted for inflation. 
                  This is the price consumers actually pay at the register.
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Use case:</span> Understanding 
                  current market conditions and short-term price movements.
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="hours-of-work">
            <AccordionTrigger>Hours of Work (Affordability)</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3">
                <div className="bg-muted p-3 rounded font-mono text-sm">
                  hours_of_work = (price_per_unit × quantity) ÷ hourly_wage
                </div>
                <p className="text-sm text-muted-foreground">
                  Expresses price in terms of labor time required to purchase an item. This 
                  normalizes prices against earning power, making it easier to compare 
                  affordability across time periods with different wage levels.
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Example:</span> If eggs cost 
                  $4.00/dozen and your wage is $20/hour, eggs cost 0.20 hours of work (12 minutes).
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Limitations:</span> Assumes 
                  consistent work hours and doesn't account for taxes, benefits, or employment status.
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="real">
            <AccordionTrigger>Real Price (CPI-Adjusted)</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3">
                <div className="bg-muted p-3 rounded font-mono text-sm">
                  real_price = (nominal_price ÷ CPI_value) × 100
                </div>
                <p className="text-sm text-muted-foreground">
                  Adjusts historical prices to a common baseline (1982-84 = 100) using the Consumer 
                  Price Index from the Bureau of Labor Statistics. This removes the effect of general 
                  inflation to show "real" purchasing power changes over time.
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Example:</span> If milk costs $4.50 
                  today and the CPI is 300, the real price is ($4.50 ÷ 300) × 100 = $1.50 in 1982-84 dollars.
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Limitations:</span> CPI measures 
                  general inflation across all consumer goods. Individual item price changes may 
                  differ significantly from overall inflation rates.
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="inflation">
            <AccordionTrigger>Inflation Rate</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3">
                <div className="bg-muted p-3 rounded font-mono text-sm">
                  inflation_rate = ((new_CPI - old_CPI) / old_CPI) × 100
                </div>
                <p className="text-sm text-muted-foreground">
                  Measures the percentage change in the Consumer Price Index between two time periods, 
                  indicating the rate of general price increases across the economy.
                </p>
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Note:</span> This is distinct from 
                  individual item price changes, which can vary significantly from the overall inflation rate.
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="change">
            <AccordionTrigger>Price Change Calculations</AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3">
                <div className="bg-muted p-3 rounded font-mono text-sm">
                  percent_change = ((new_price - old_price) / old_price) × 100
                  <br />
                  CAGR = ((end_price / start_price)^(1/years) - 1) × 100
                </div>
                <p className="text-sm text-muted-foreground">
                  Simple percentage change for year-over-year comparisons. Compound Annual Growth 
                  Rate (CAGR) for longer periods to smooth volatility.
                </p>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Data Sources</h2>
        <div className="space-y-4">
          {SOURCES.map(source => (
            <Card key={source.id} className="p-4 bg-muted/30">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold mb-1">{source.name}</h3>
                    <p className="text-sm text-muted-foreground">{source.provider}</p>
                  </div>
                  <Badge variant="secondary">{source.license}</Badge>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock size={14} />
                    <span>Retrieved: {new Date(source.retrievalTimestamp).toLocaleDateString()}</span>
                  </div>
                  <a 
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-accent hover:underline"
                  >
                    <LinkIcon size={14} />
                    <span>View Source</span>
                  </a>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Known Limitations</h2>
        <div className="space-y-3 text-sm text-muted-foreground">
          <div className="flex gap-3">
            <span className="font-bold text-foreground">•</span>
            <p>
              <span className="font-medium text-foreground">Regional Coverage:</span> National 
              averages may not reflect local price variations. State and metro-level data 
              availability varies by item.
            </p>
          </div>
          <div className="flex gap-3">
            <span className="font-bold text-foreground">•</span>
            <p>
              <span className="font-medium text-foreground">Quality Variation:</span> Prices 
              represent standardized grades (e.g., USDA Choice beef, Grade A eggs) and may not 
              match specific retail products.
            </p>
          </div>
          <div className="flex gap-3">
            <span className="font-bold text-foreground">•</span>
            <p>
              <span className="font-medium text-foreground">Temporal Lag:</span> Government data 
              series may have reporting delays. Check source timestamps for data freshness.
            </p>
          </div>
          <div className="flex gap-3">
            <span className="font-bold text-foreground">•</span>
            <p>
              <span className="font-medium text-foreground">Wage Assumptions:</span> Hours-of-work 
              calculations assume consistent hourly wages and don't account for taxes, benefits, 
              or part-time/seasonal employment patterns.
            </p>
          </div>
          <div className="flex gap-3">
            <span className="font-bold text-foreground">•</span>
            <p>
              <span className="font-medium text-foreground">Basket Composition:</span> The 
              "essential basket" is a curated subset and not a complete market basket for 
              inflation measurement.
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-accent/10 border-accent">
        <h3 className="font-semibold mb-2">Claims vs Evidence</h3>
        <div className="space-y-2 text-sm">
          <p>
            <span className="font-medium text-foreground">What the data shows:</span>{' '}
            <span className="text-muted-foreground">
              Historical price series for specific commodities and their relationship to wage rates 
              over time.
            </span>
          </p>
          <p>
            <span className="font-medium text-foreground">What it cannot prove:</span>{' '}
            <span className="text-muted-foreground">
              Causation, individual purchasing decisions, policy recommendations, or economic 
              predictions. This tool visualizes relationships but does not establish causal mechanisms.
            </span>
          </p>
          <p>
            <span className="font-medium text-foreground">Interpretation responsibility:</span>{' '}
            <span className="text-muted-foreground">
              Users should apply appropriate context, consider confounding factors, and consult 
              multiple sources for policy or research conclusions.
            </span>
          </p>
        </div>
      </Card>
    </div>
  )
}
