import type {
  Generation,
  GenerationDefinition,
  EconomicEvent,
  DialoguePrompt,
  DataGuardrails,
  AffordabilityByAge,
  VolatilityMetrics,
  DecadeComparison,
  EconomicLearningModule
} from './types'
import { ITEMS, getWageHistory, getPriceHistory, getCPIHistory } from './data'

export const GENERATIONS: GenerationDefinition[] = [
  {
    id: 'silent',
    name: 'Silent Generation',
    birthYearStart: 1928,
    birthYearEnd: 1945,
    description: 'Born during the Great Depression and WWII; experienced post-war prosperity and the golden age of American manufacturing',
    color: 'oklch(0.60 0.15 280)'
  },
  {
    id: 'boomer',
    name: 'Baby Boomers',
    birthYearStart: 1946,
    birthYearEnd: 1964,
    description: 'Born during post-war economic expansion; witnessed stagflation, rising homeownership, and transition to service economy',
    color: 'oklch(0.58 0.18 240)'
  },
  {
    id: 'genx',
    name: 'Generation X',
    birthYearStart: 1965,
    birthYearEnd: 1980,
    description: 'Came of age during economic restructuring; experienced tech boom/bust, rising education costs, and early globalization',
    color: 'oklch(0.62 0.20 180)'
  },
  {
    id: 'millennial',
    name: 'Millennials',
    birthYearStart: 1981,
    birthYearEnd: 1996,
    description: 'Entered workforce during 2008 financial crisis; faced high student debt, housing affordability challenges, and gig economy',
    color: 'oklch(0.60 0.18 140)'
  },
  {
    id: 'genz',
    name: 'Generation Z',
    birthYearStart: 1997,
    birthYearEnd: 2012,
    description: 'Digital natives coming of age during COVID-19 pandemic; experiencing inflation volatility and evolving work models',
    color: 'oklch(0.58 0.20 60)'
  }
]

export const ECONOMIC_EVENTS: EconomicEvent[] = [
  {
    id: 'recession-1953',
    name: 'Post-Korean War Recession',
    date: '1953-07-01',
    endDate: '1954-05-01',
    type: 'recession',
    description: 'Economic contraction following end of Korean War; reduction in government defense spending led to 10-month recession',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'recession-1957',
    name: '1957-58 Recession',
    date: '1957-08-01',
    endDate: '1958-04-01',
    type: 'recession',
    description: 'Moderate recession characterized by tight monetary policy and reduced business investment',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'recession-1960',
    name: '1960-61 Recession',
    date: '1960-04-01',
    endDate: '1961-02-01',
    type: 'recession',
    description: 'Brief recession triggered by Federal Reserve tightening to defend dollar under Bretton Woods',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'oil-shock-1973',
    name: 'Oil Embargo & Price Shock',
    date: '1973-10-01',
    endDate: '1974-03-01',
    type: 'shock',
    description: 'OPEC oil embargo caused crude oil prices to quadruple; contributed to stagflation period',
    citation: 'Federal Reserve History: Oil Shock of 1973-74',
    citationUrl: 'https://www.federalreservehistory.org/essays/oil-shock-of-1973-74',
    source: 'Federal Reserve'
  },
  {
    id: 'recession-1973',
    name: '1973-75 Recession',
    date: '1973-11-01',
    endDate: '1975-03-01',
    type: 'recession',
    description: 'Severe recession marked by stagflation—simultaneous high inflation and unemployment',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'oil-shock-1979',
    name: 'Iranian Revolution Oil Shock',
    date: '1979-01-01',
    endDate: '1980-12-01',
    type: 'shock',
    description: 'Iranian Revolution disrupted oil supply; crude oil prices doubled contributing to inflation spike',
    citation: 'Federal Reserve History: Oil Shock of 1978-79',
    citationUrl: 'https://www.federalreservehistory.org/essays/oil-shock-of-1978-79',
    source: 'Federal Reserve'
  },
  {
    id: 'recession-1980',
    name: '1980 Recession',
    date: '1980-01-01',
    endDate: '1980-07-01',
    type: 'recession',
    description: 'Brief but sharp recession as Federal Reserve raised interest rates to combat inflation',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'recession-1981',
    name: 'Early 1980s Recession',
    date: '1981-07-01',
    endDate: '1982-11-01',
    type: 'recession',
    description: 'Severe recession caused by aggressive monetary tightening under Fed Chair Paul Volcker to break inflation; unemployment reached 10.8%',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'recession-1990',
    name: '1990-91 Recession',
    date: '1990-07-01',
    endDate: '1991-03-01',
    type: 'recession',
    description: 'Recession triggered by Iraq invasion of Kuwait, oil price spike, and savings & loan crisis',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'dotcom-bust-2001',
    name: 'Dot-com Bubble Burst',
    date: '2001-03-01',
    endDate: '2001-11-01',
    type: 'crisis',
    description: 'Collapse of internet stock valuations; tech-heavy NASDAQ fell 78% from peak',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'financial-crisis-2008',
    name: 'Financial Crisis & Great Recession',
    date: '2007-12-01',
    endDate: '2009-06-01',
    type: 'crisis',
    description: 'Severe recession triggered by housing bubble collapse and financial system crisis; longest recession since Great Depression',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'covid-recession-2020',
    name: 'COVID-19 Pandemic Recession',
    date: '2020-02-01',
    endDate: '2020-04-01',
    type: 'crisis',
    description: 'Sharpest economic contraction on record; brief but severe recession caused by pandemic lockdowns',
    citation: 'NBER Business Cycle Dating Committee',
    citationUrl: 'https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions',
    source: 'National Bureau of Economic Research'
  },
  {
    id: 'inflation-spike-2021',
    name: 'Post-Pandemic Inflation Surge',
    date: '2021-03-01',
    type: 'shock',
    description: 'Rapid inflation acceleration driven by supply chain disruptions, labor shortages, and demand surge',
    citation: 'BLS Consumer Price Index Summary',
    citationUrl: 'https://www.bls.gov/cpi/',
    source: 'Bureau of Labor Statistics'
  }
]

export const DIALOGUE_PROMPTS: DialoguePrompt[] = [
  {
    id: 'affordability-age-25',
    category: 'affordability',
    question: 'How did affordability of essential goods at age 25 differ between someone born in 1950 versus someone born in 1990?',
    context: 'This prompt explores purchasing power at early career stage across generations, accounting for both wage levels and price levels at the corresponding calendar years (1975 vs 2015).',
    relatedChartIds: ['generational-affordability', 'life-stage-comparison'],
    educatorNotes: 'Encourage participants to consider structural economic factors (globalization, technology, policy) rather than attributing differences to generational character or work ethic.'
  },
  {
    id: 'volatility-experience',
    category: 'volatility',
    question: 'Which generation experienced the highest price volatility during their peak earning years (ages 35-55)?',
    context: 'This examines economic stability during critical wealth-building period, comparing volatility metrics across different cohorts\' career phases.',
    relatedChartIds: ['volatility-timeline', 'generation-volatility'],
    educatorNotes: 'Discuss how volatility affects financial planning, savings behavior, and risk tolerance. Avoid framing volatility as intentional rather than systemic.'
  },
  {
    id: 'wage-growth-eras',
    category: 'wages',
    question: 'How did wage growth rates compare across the 1960s-70s, 1980s-90s, and 2000s-2020s?',
    context: 'Explores whether minimum and median wages kept pace with essential goods prices across different economic eras.',
    relatedChartIds: ['decades-comparison', 'wage-vs-basket-timeline'],
    educatorNotes: 'Connect wage trends to documented economic policies (trade, labor law, monetary policy) using neutral language and credible sources.'
  },
  {
    id: 'housing-education-comparison',
    category: 'affordability',
    question: 'If housing and education were tracked like essential goods, how would affordability trends compare to food and fuel?',
    context: 'Prompts discussion about which categories of expenses have outpaced wage growth most significantly.',
    relatedChartIds: ['item-outpacing-rankings'],
    educatorNotes: 'Future feature placeholder—currently limited to food/fuel basket. Discuss data availability challenges for consistent historical housing/education pricing.'
  },
  {
    id: 'event-impact',
    category: 'general',
    question: 'How did the 1973 oil shock, 2008 financial crisis, and 2020 pandemic differ in their impact on essential goods affordability?',
    context: 'Compares three major economic disruptions across different decades, examining both immediate and lasting effects.',
    relatedChartIds: ['event-overlay-timeline', 'event-impact-comparison'],
    educatorNotes: 'Emphasize documented causal mechanisms (supply disruption, demand shock, policy response) rather than speculation about coordination.'
  },
  {
    id: 'multigenerational-perspective',
    category: 'general',
    question: 'What economic experiences from your generation do you wish other generations better understood?',
    context: 'Open-ended prompt designed for family or classroom discussion, encouraging empathy and shared storytelling grounded in data context.',
    relatedChartIds: ['generational-dashboard'],
    educatorNotes: 'Create space for personal narratives while anchoring discussion in objective data. Validate each generation\'s experiences as shaped by structural conditions.'
  }
]

export function getGenerationByBirthYear(birthYear: number): Generation | null {
  const gen = GENERATIONS.find(
    g => birthYear >= g.birthYearStart && birthYear <= g.birthYearEnd
  )
  return gen?.id || null
}

export function getGenerationColor(generation: Generation): string {
  return GENERATIONS.find(g => g.id === generation)?.color || 'oklch(0.5 0.1 200)'
}

export function calculateVolatilityMetrics(
  data: Array<{ date: string; value: number }>,
  windowYears: 3 | 5 | 10,
  metric: 'price' | 'wage' | 'basket' | 'cpi',
  itemId?: string
): VolatilityMetrics[] {
  const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date))
  const volatilityData: VolatilityMetrics[] = []
  
  const windowMonths = windowYears * 12
  
  for (let i = windowMonths; i < sorted.length; i++) {
    const windowData = sorted.slice(i - windowMonths, i)
    
    const annualizedChanges: number[] = []
    for (let j = 1; j < windowData.length; j++) {
      if (windowData[j - 1].value > 0 && windowData[j].value > 0) {
        const change = (windowData[j].value - windowData[j - 1].value) / windowData[j - 1].value
        const monthsElapsed = 1
        const annualized = change * (12 / monthsElapsed)
        annualizedChanges.push(annualized)
      }
    }
    
    if (annualizedChanges.length > 0) {
      const mean = annualizedChanges.reduce((sum, val) => sum + val, 0) / annualizedChanges.length
      const variance = annualizedChanges.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / annualizedChanges.length
      const stdDev = Math.sqrt(variance)
      
      volatilityData.push({
        date: sorted[i].date,
        value: stdDev,
        volatilityWindow: windowYears,
        metric,
        itemId
      })
    }
  }
  
  return volatilityData
}

export function calculateAffordabilityByAge(
  birthYear: number,
  ages: number[],
  basketItemIds: string[]
): AffordabilityByAge[] {
  const generation = getGenerationByBirthYear(birthYear)
  if (!generation) return []
  
  const results: AffordabilityByAge[] = []
  
  for (const age of ages) {
    const calendarYear = birthYear + age
    const dateStr = `${calendarYear}-06-01`
    
    const wageData = getWageHistory('minimum', 'US-National')
    const wagePoint = wageData.find(w => w.date <= dateStr && w.date >= `${calendarYear - 1}-01-01`)
    const wage = wagePoint?.wageValue || 15
    
    let basketCost = 0
    let interpolated = false
    
    for (const itemId of basketItemIds) {
      const priceHistory = getPriceHistory(itemId)
      const pricePoint = priceHistory.find(p => p.date >= `${calendarYear - 1}-01-01` && p.date <= `${calendarYear + 1}-12-31`)
      
      if (pricePoint) {
        basketCost += pricePoint.nominalPrice
      } else {
        interpolated = true
        const avgPrice = priceHistory.length > 0
          ? priceHistory.reduce((sum, p) => sum + p.nominalPrice, 0) / priceHistory.length
          : 5
        basketCost += avgPrice
      }
    }
    
    const basketHours = basketCost / wage
    
    results.push({
      generation,
      birthYear,
      age,
      calendarYear,
      basketHours,
      wage,
      basketCost,
      interpolated
    })
  }
  
  return results
}

export function generateDecadeComparisons(basketItemIds: string[]): DecadeComparison[] {
  const decades: DecadeComparison[] = []
  
  for (let startYear = 1950; startYear <= 2020; startYear += 10) {
    const endYear = startYear + 9
    const decade = `${startYear}s`
    
    const wageData = getWageHistory('minimum', 'US-National')
    const decadeWages = wageData.filter(w => {
      const year = parseInt(w.date.substring(0, 4))
      return year >= startYear && year <= endYear
    })
    
    const medianWage = decadeWages.length > 0
      ? decadeWages.reduce((sum, w) => sum + w.wageValue, 0) / decadeWages.length
      : 0
    
    let basketCost = 0
    let dataPoints = 0
    
    for (const itemId of basketItemIds) {
      const priceHistory = getPriceHistory(itemId)
      const decadePrices = priceHistory.filter(p => {
        const year = parseInt(p.date.substring(0, 4))
        return year >= startYear && year <= endYear
      })
      
      if (decadePrices.length > 0) {
        const avgPrice = decadePrices.reduce((sum, p) => sum + p.nominalPrice, 0) / decadePrices.length
        basketCost += avgPrice
        dataPoints += decadePrices.length
      }
    }
    
    const basketHours = medianWage > 0 ? basketCost / medianWage : 0
    const coverage = dataPoints / (basketItemIds.length * 10)
    
    const cpiData = getCPIHistory('US-National')
    const decadeCPI = cpiData.filter(c => {
      const year = parseInt(c.date.substring(0, 4))
      return year >= startYear && year <= endYear
    })
    const cpiAverage = decadeCPI.length > 0
      ? decadeCPI.reduce((sum, c) => sum + c.value, 0) / decadeCPI.length
      : 0
    
    decades.push({
      decade,
      startYear,
      endYear,
      medianWage,
      basketCost,
      basketHours,
      cpiAverage,
      volatilityAverage: 0,
      coverage
    })
  }
  
  return decades
}

export const DATA_GUARDRAILS: Record<string, DataGuardrails> = {
  'volatility-timeline': {
    chartId: 'volatility-timeline',
    whatDataShows: [
      'Standard deviation of annualized price/wage changes over selected rolling window',
      'Periods of higher vs lower economic fluctuation as measured by observed data',
      'Correlation between documented events (recessions, shocks) and volatility spikes'
    ],
    whatDataDoesNotShow: [
      'Intent or coordination behind volatility patterns',
      'Whether volatility was avoidable or intentional',
      'Predictions about future volatility'
    ],
    assumptions: [
      'Volatility calculated using standard statistical methods (rolling window standard deviation)',
      'Data quality and coverage varies by time period; earlier decades have sparser data',
      'Window length (3/5/10 year) affects sensitivity to short-term vs long-term patterns'
    ],
    limitations: [
      'Does not account for regional variation within national data',
      'Essential goods basket composition held constant; actual consumption patterns evolved',
      'Does not capture all dimensions of economic uncertainty (employment volatility, etc.)'
    ]
  },
  'generational-affordability': {
    chartId: 'generational-affordability',
    whatDataShows: [
      'Hours of work required to purchase essential basket at specific ages and calendar years',
      'How wage levels and price levels varied across different cohorts\' life stages',
      'Observed differences in purchasing power between generations at comparable ages'
    ],
    whatDataDoesNotShow: [
      'Why wages or prices differed (does not establish causation)',
      'Whether any generation is "at fault" for economic conditions',
      'Full picture of economic wellbeing (excludes wealth, benefits, non-basket expenses)'
    ],
    assumptions: [
      'Uses minimum or median wage as proxy; individual wages vary significantly',
      'Basket held constant; actual consumption and preferences differ by generation',
      'Some data points interpolated where historical data unavailable (marked explicitly)'
    ],
    limitations: [
      'Does not account for non-wage benefits, wealth accumulation, or transfer payments',
      'Cannot capture subjective economic experience or cultural factors',
      'Regional and demographic variation not fully represented'
    ]
  },
  'event-overlay': {
    chartId: 'event-overlay',
    whatDataShows: [
      'Timing of documented economic events relative to price/wage/volatility trends',
      'Correlation between events and observed economic metrics',
      'Historical context for periods of economic disruption'
    ],
    whatDataDoesNotShow: [
      'Proof of causation (correlation does not establish cause)',
      'Whether events were preventable or intentionally caused',
      'Complete explanation of complex economic dynamics'
    ],
    assumptions: [
      'Event dates and descriptions sourced from credible academic and government sources',
      'Event categorization (recession, shock, etc.) follows standard economic definitions',
      'Multiple factors typically influence economic conditions simultaneously'
    ],
    limitations: [
      'Event annotations necessarily simplify complex historical phenomena',
      'Not all relevant economic factors captured by selected events',
      'Academic consensus on causes and effects may evolve with new research'
    ]
  }
}

export const LEARNING_MODULES: EconomicLearningModule[] = [
  {
    id: 'business-cycles',
    title: 'Economic Cycles: Expansion and Contraction',
    category: 'cycles',
    content: `Economic cycles, also called business cycles, are recurring patterns of expansion (growth) and contraction (recession) in economic activity. During expansions, employment rises, incomes grow, and production increases. During contractions, the opposite occurs—unemployment rises and output declines.

These cycles are driven by multiple factors: changes in consumer and business confidence, monetary policy decisions by the Federal Reserve, fiscal policy changes, technological innovation, and external shocks like oil price spikes or pandemics.

Importantly, cycles are a normal feature of market economies. While recessions cause hardship, they also reflect economic adjustments as markets respond to changing conditions. The National Bureau of Economic Research (NBER) officially dates U.S. business cycles using multiple economic indicators.`,
    readingLevel: 10,
    citations: [
      {
        text: 'NBER Business Cycle Dating',
        url: 'https://www.nber.org/research/business-cycle-dating',
        source: 'National Bureau of Economic Research'
      },
      {
        text: 'Federal Reserve: What is a business cycle?',
        url: 'https://www.federalreserve.gov/faqs/what-is-a-business-cycle.htm',
        source: 'Federal Reserve'
      }
    ],
    relatedTerms: ['recession', 'expansion', 'GDP', 'unemployment']
  },
  {
    id: 'inflation-basics',
    title: 'Understanding Inflation',
    category: 'inflation',
    content: `Inflation is the rate at which the general level of prices rises over time. When inflation occurs, each dollar buys fewer goods and services. The Consumer Price Index (CPI) measures inflation by tracking the cost of a representative basket of goods and services.

Inflation can result from demand-pull factors (when demand exceeds supply), cost-push factors (when production costs rise), or monetary expansion (when money supply grows faster than economic output). Moderate inflation (2-3% annually) is typical in healthy economies. High inflation erodes purchasing power; deflation (falling prices) can signal economic weakness.

The Federal Reserve attempts to maintain stable inflation around 2% through monetary policy—adjusting interest rates and money supply to influence economic activity.`,
    readingLevel: 10,
    citations: [
      {
        text: 'BLS Consumer Price Index FAQs',
        url: 'https://www.bls.gov/cpi/questions-and-answers.htm',
        source: 'Bureau of Labor Statistics'
      },
      {
        text: 'Federal Reserve: Why does the Fed aim for 2% inflation?',
        url: 'https://www.federalreserve.gov/faqs/economy_14400.htm',
        source: 'Federal Reserve'
      }
    ],
    relatedTerms: ['CPI', 'deflation', 'purchasing power', 'monetary policy']
  },
  {
    id: 'monetary-policy',
    title: 'Monetary Policy: Tightening and Loosening',
    category: 'monetary-policy',
    content: `Monetary policy refers to actions by a central bank (in the U.S., the Federal Reserve) to influence money supply and interest rates to achieve economic goals like full employment and stable prices.

**Tightening** (contractionary policy) involves raising interest rates and reducing money supply to slow economic activity and reduce inflation. This makes borrowing more expensive, which can cool demand.

**Loosening** (expansionary policy) involves lowering interest rates and increasing money supply to stimulate economic activity during recessions. This makes borrowing cheaper, encouraging spending and investment.

These policy shifts affect consumers directly through mortgage rates, credit card rates, and savings returns. They also influence business investment decisions and employment levels. The Federal Reserve adjusts policy based on economic data, not political considerations.`,
    readingLevel: 10,
    citations: [
      {
        text: 'Federal Reserve: Monetary Policy Principles and Practice',
        url: 'https://www.federalreserve.gov/monetarypolicy.htm',
        source: 'Federal Reserve'
      },
      {
        text: 'Federal Reserve Education: How Monetary Policy Works',
        url: 'https://www.federalreserveeducation.org/about-the-fed/structure-and-functions/monetary-policy',
        source: 'Federal Reserve'
      }
    ],
    relatedTerms: ['interest rates', 'Federal Reserve', 'inflation', 'recession']
  },
  {
    id: 'supply-shocks',
    title: 'Supply Shocks and Price Volatility',
    category: 'supply-shocks',
    content: `Supply shocks are sudden, unexpected events that disrupt the production or availability of goods and services. Examples include natural disasters, oil embargoes, pandemics, and geopolitical conflicts.

When supply is disrupted while demand remains constant, prices typically rise sharply. The 1973 and 1979 oil shocks are classic examples—OPEC supply restrictions caused crude oil prices to spike, affecting not just gasoline but all goods requiring energy for production or transportation.

Supply shocks differ from demand-driven price changes because they originate from external disruptions rather than changing consumer behavior. They often cause temporary volatility, though some shocks (like energy crises) can have lasting effects on economic structure.

Understanding supply shocks helps explain price volatility without assuming coordination or intent. Most supply disruptions result from geopolitical events, natural phenomena, or unintended consequences of policy decisions.`,
    readingLevel: 10,
    citations: [
      {
        text: 'Federal Reserve History: Oil Shock of 1973-74',
        url: 'https://www.federalreservehistory.org/essays/oil-shock-of-1973-74',
        source: 'Federal Reserve'
      },
      {
        text: 'IMF: Supply Shocks and Economic Policy',
        url: 'https://www.imf.org/external/pubs/ft/issues/issues21/',
        source: 'International Monetary Fund'
      }
    ],
    relatedTerms: ['oil shock', 'inflation', 'OPEC', 'stagflation']
  },
  {
    id: 'media-amplification',
    title: 'Media Coverage and Economic Perception',
    category: 'media',
    content: `Media coverage of economic news can influence how people perceive and react to economic conditions. Research shows that negative economic news tends to receive more coverage than positive news, potentially amplifying perceptions of crisis.

This "negativity bias" in news coverage is not a conspiracy—it reflects journalistic norms (conflict and problems are newsworthy) and audience psychology (people pay more attention to threats). However, it can create a gap between objective economic indicators and subjective economic anxiety.

During periods of volatility, saturation coverage can intensify uncertainty and affect consumer confidence, which in turn influences spending and investment decisions. This creates feedback loops where perception affects reality.

Critical media literacy involves: (1) checking whether reporting cites credible data sources, (2) distinguishing between objective indicators and opinion/prediction, (3) recognizing that individual experiences vary from aggregate statistics, and (4) understanding that uncertainty is inherent to economic forecasting.`,
    readingLevel: 10,
    citations: [
      {
        text: 'Pew Research: Economic News and Public Perception',
        url: 'https://www.pewresearch.org/journalism/',
        source: 'Pew Research Center'
      },
      {
        text: 'American Economic Review: Media Sentiment and Consumer Confidence',
        url: 'https://www.aeaweb.org/articles',
        source: 'American Economic Association'
      }
    ],
    relatedTerms: ['consumer confidence', 'economic anxiety', 'negativity bias']
  }
]
