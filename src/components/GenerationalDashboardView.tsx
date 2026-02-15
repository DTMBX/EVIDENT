import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Users, TrendUp, ChartLine, Info, Calendar, ChartBar } from '@phosphor-icons/react'
import { GENERATIONS, getGenerationByBirthYear, calculateAffordabilityByAge, DIALOGUE_PROMPTS, DATA_GUARDRAILS } from '@/lib/generational-data'
import { ITEMS } from '@/lib/data'
import type { Generation } from '@/lib/types'

export function GenerationalDashboardView() {
  const [selectedGenerations, setSelectedGenerations] = useState<Generation[]>(['boomer', 'genx', 'millennial'])
  const [selectedBirthYear, setSelectedBirthYear] = useState<number>(1980)
  const [showGuardrails, setShowGuardrails] = useState(true)

  const currentGeneration = getGenerationByBirthYear(selectedBirthYear)
  const basketItemIds = ITEMS.slice(0, 8).map(i => i.id)
  
  const affordabilityData = calculateAffordabilityByAge(
    selectedBirthYear,
    [25, 35, 45, 55],
    basketItemIds
  )

  const guardrails = DATA_GUARDRAILS['generational-affordability']

  const dialoguePrompts = DIALOGUE_PROMPTS.filter(p => 
    p.category === 'affordability' || p.category === 'general'
  ).slice(0, 3)

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-start justify-between gap-3 sm:gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-foreground mb-1 sm:mb-2">
            Generational Economic Timeline
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground max-w-3xl">
            Explore how economic experiences differ by birth cohort. Compare affordability, volatility, and wage dynamics across generations to build shared understanding through data.
          </p>
        </div>
      </div>

      <Alert className="border-accent/30 bg-accent/5">
        <Info className="h-4 w-4 text-accent flex-shrink-0" />
        <AlertDescription className="text-xs sm:text-sm">
          <strong>Educational Tool:</strong> This platform promotes civic literacy and cross-generational empathy by showing observed economic patterns. 
          It separates documented data from interpretation and does not attribute intent or assign blame.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <Card className="p-4 sm:p-6 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4 sm:mb-6">
            <Users className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
            <h2 className="font-display text-lg sm:text-xl font-semibold">Select Your Birth Year</h2>
          </div>

          <div className="space-y-3 sm:space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Birth Year</label>
              <Select
                value={selectedBirthYear.toString()}
                onValueChange={(val) => setSelectedBirthYear(parseInt(val))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: 95 }, (_, i) => 1928 + i).map(year => {
                    const gen = getGenerationByBirthYear(year)
                    const genDef = GENERATIONS.find(g => g.id === gen)
                    return (
                      <SelectItem key={year} value={year.toString()}>
                        {year} {genDef && `(${genDef.name})`}
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
            </div>

            {currentGeneration && (
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Badge 
                    style={{ 
                      backgroundColor: GENERATIONS.find(g => g.id === currentGeneration)?.color 
                    }}
                    className="text-white"
                  >
                    {GENERATIONS.find(g => g.id === currentGeneration)?.name}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {GENERATIONS.find(g => g.id === currentGeneration)?.description}
                </p>
              </div>
            )}

            <Separator />

            <div>
              <h3 className="font-display font-semibold mb-3">Affordability at Key Life Stages</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Hours of work required to purchase essential goods basket at different ages:
              </p>

              <div className="space-y-3">
                {affordabilityData.map((data) => (
                  <div 
                    key={data.age} 
                    className="flex items-center justify-between p-3 bg-background border rounded-lg"
                  >
                    <div>
                      <div className="font-medium">Age {data.age}</div>
                      <div className="text-xs text-muted-foreground">
                        Calendar year: {data.calendarYear}
                        {data.interpolated && (
                          <Badge variant="outline" className="ml-2 text-xs">
                            Interpolated
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-lg font-bold">
                        {data.basketHours.toFixed(1)} hrs
                      </div>
                      <div className="text-xs text-muted-foreground">
                        ${data.basketCost.toFixed(2)} @ ${data.wage.toFixed(2)}/hr
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <ChartLine className="w-5 h-5 text-accent" />
              <h3 className="font-display font-semibold">Quick Insights</h3>
            </div>
            <div className="space-y-4 text-sm">
              <div>
                <div className="font-medium mb-1">Generation Count</div>
                <div className="text-2xl font-mono font-bold text-primary">
                  {GENERATIONS.length}
                </div>
                <div className="text-xs text-muted-foreground">Silent → Gen Z</div>
              </div>
              <Separator />
              <div>
                <div className="font-medium mb-1">Coverage Period</div>
                <div className="text-lg font-mono font-bold">1950–Present</div>
                <div className="text-xs text-muted-foreground">74+ years of data</div>
              </div>
              <Separator />
              <div>
                <div className="font-medium mb-1">Essential Items Tracked</div>
                <div className="text-2xl font-mono font-bold text-accent">
                  {ITEMS.length}
                </div>
                <div className="text-xs text-muted-foreground">Food, fuel, household</div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-5 h-5 text-primary" />
              <h3 className="font-display font-semibold">Compare Generations</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Select multiple generations to compare affordability at equivalent life stages.
            </p>
            <Button variant="secondary" className="w-full" size="sm">
              <ChartBar className="w-4 h-4 mr-2" />
              View Comparison Tool
            </Button>
          </Card>
        </div>
      </div>

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

          <Separator className="my-4" />

          <div>
            <h4 className="font-semibold text-sm mb-2">Assumptions & Limitations</h4>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              {guardrails.assumptions.map((item, i) => (
                <li key={i} className="flex gap-2">
                  <span>•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      )}

      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-primary" />
          <h3 className="font-display text-lg font-semibold">Civic Dialogue Prompts</h3>
        </div>
        <p className="text-sm text-muted-foreground mb-6">
          Use these data-grounded questions to start respectful conversations about economic experiences across generations.
        </p>

        <div className="grid gap-4">
          {dialoguePrompts.map((prompt) => (
            <div key={prompt.id} className="p-4 border rounded-lg hover:border-accent/50 transition-colors">
              <div className="flex items-start gap-3">
                <Badge variant="outline" className="mt-1">
                  {prompt.category}
                </Badge>
                <div className="flex-1">
                  <p className="font-medium mb-2">{prompt.question}</p>
                  <p className="text-sm text-muted-foreground">{prompt.context}</p>
                  {prompt.educatorNotes && (
                    <details className="mt-3">
                      <summary className="text-sm font-medium cursor-pointer text-accent hover:text-accent/80">
                        Educator Notes
                      </summary>
                      <p className="text-sm text-muted-foreground mt-2 pl-4 border-l-2 border-accent/20">
                        {prompt.educatorNotes}
                      </p>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 p-4 bg-accent/5 border border-accent/20 rounded-lg">
          <p className="text-sm">
            <strong>Discussion Guidelines:</strong> These prompts promote empathy and understanding by exploring how structural economic forces shaped different generations' experiences. 
            Avoid framing differences as individual or generational fault.
          </p>
        </div>
      </Card>
    </div>
  )
}
