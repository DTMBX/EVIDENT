import type { Item, PricePoint, WageSeries, Source, CPIDataPoint } from './types'

export const SOURCES: Source[] = [
  {
    id: 'usda-1',
    name: 'USDA Agricultural Marketing Service',
    provider: 'U.S. Department of Agriculture',
    license: 'Public Domain',
    terms: 'Data provided as-is for informational purposes.',
    url: 'https://www.ams.usda.gov/market-news',
    retrievalTimestamp: new Date().toISOString(),
    isOfficial: true,
    reliabilityTier: 'tier-1',
    refreshSchedule: 'daily',
    coverageMap: { 'US-National': ['eggs-dozen', 'milk-gallon', 'butter-lb', 'cheese-lb'] },
    seriesIdentifiers: ['DA_RF100'],
    status: 'active',
  },
  {
    id: 'eia-1',
    name: 'U.S. Energy Information Administration',
    provider: 'U.S. Department of Energy',
    license: 'Public Domain',
    terms: 'EIA provides energy data as a public service.',
    url: 'https://www.eia.gov/',
    retrievalTimestamp: new Date().toISOString(),
    isOfficial: true,
    reliabilityTier: 'tier-1',
    refreshSchedule: 'daily',
    coverageMap: { 'US-National': ['gasoline-gallon', 'propane-gallon'] },
    seriesIdentifiers: ['PET.EMM_EPM0_PTE_NUS_DPG.M'],
    status: 'active',
  },
  {
    id: 'bls-1',
    name: 'Bureau of Labor Statistics - Wage Data',
    provider: 'U.S. Department of Labor',
    license: 'Public Domain',
    terms: 'Official BLS wage statistics.',
    url: 'https://www.bls.gov/',
    retrievalTimestamp: new Date().toISOString(),
    isOfficial: true,
    reliabilityTier: 'tier-1',
    refreshSchedule: 'daily',
    coverageMap: { 'US-National': ['minimum-wage', 'median-wage'] },
    seriesIdentifiers: ['CES0500000003'],
    status: 'active',
  },
  {
    id: 'bls-cpi',
    name: 'Bureau of Labor Statistics - Consumer Price Index',
    provider: 'U.S. Department of Labor',
    license: 'Public Domain',
    terms: 'Official CPI published by BLS.',
    url: 'https://www.bls.gov/cpi/',
    retrievalTimestamp: new Date().toISOString(),
    isOfficial: true,
    reliabilityTier: 'tier-1',
    refreshSchedule: 'daily',
    coverageMap: { 'US-National': ['cpi-all-items'] },
    seriesIdentifiers: ['CUUR0000SA0'],
    status: 'active',
  }
]

export const ITEMS: Item[] = [
  {
    id: 'eggs-dozen',
    name: 'Eggs',
    category: 'dairy',
    unitStandard: 'dozen',
    acceptableAlternateUnits: [],
    conversions: [],
    description: 'Grade A large eggs',
    sourceSeriesIds: ['usda-1'],
    regionCoverage: ['US-National'],
  },
  {
    id: 'milk-gallon',
    name: 'Milk',
    category: 'dairy',
    unitStandard: 'gallon',
    acceptableAlternateUnits: [],
    conversions: [],
    description: 'Whole milk, conventional',
    sourceSeriesIds: ['usda-1'],
    regionCoverage: ['US-National'],
  },
  {
    id: 'butter-lb',
    name: 'Butter',
    category: 'dairy',
    unitStandard: 'lb',
    acceptableAlternateUnits: [],
    conversions: [],
    description: 'Salted butter',
    sourceSeriesIds: ['usda-1'],
    regionCoverage: ['US-National'],
  },
  {
    id: 'cheese-lb',
    name: 'Cheese',
    category: 'dairy',
    unitStandard: 'lb',
    acceptableAlternateUnits: [],
    conversions: [],
    description: 'Cheddar cheese',
    sourceSeriesIds: ['usda-1'],
    regionCoverage: ['US-National'],
  },
  {
    id: 'ground-beef-lb',
    name: 'Ground Beef',
    category: 'meat',
    unitStandard: 'lb',
    acceptableAlternateUnits: [],
    conversions: [],
    description: '80% lean ground beef',
    sourceSeriesIds: ['usda-1'],
    regionCoverage: ['US-National'],
  },
  {
    id: 'tenderloin-lb',
    name: 'Beef Tenderloin',
    category: 'meat',
    unitStandard: 'lb',
    acceptableAlternateUnits: [],
    conversions: [],
    description: 'USDA Choice beef tenderloin',
    sourceSeriesIds: ['usda-1'],
    regionCoverage: ['US-National'],
  },
  {
    id: 'gasoline-gallon',
    name: 'Gasoline',
    category: 'fuel',
    unitStandard: 'gallon',
    acceptableAlternateUnits: [],
    conversions: [],
    description: 'Regular unleaded gasoline',
    sourceSeriesIds: ['eia-1'],
    regionCoverage: ['US-National'],
  },
  {
    id: 'propane-gallon',
    name: 'Propane',
    category: 'fuel',
    unitStandard: 'gallon',
    acceptableAlternateUnits: [],
    conversions: [],
    description: 'Residential propane',
    sourceSeriesIds: ['eia-1'],
    regionCoverage: ['US-National'],
  }
]

function generatePriceHistory(
  itemId: string,
  basePrice: number,
  volatility: number,
  trend: number,
  sourceId: string
): PricePoint[] {
  const points: PricePoint[] = []
  const startDate = new Date('2014-01-01')
  const endDate = new Date('2024-12-01')
  
  let currentPrice = basePrice
  let date = new Date(startDate)
  
  while (date <= endDate) {
    const randomChange = (Math.random() - 0.5) * 2 * volatility
    const trendChange = trend
    currentPrice = currentPrice * (1 + randomChange + trendChange)
    
    points.push({
      id: `${itemId}-${date.toISOString()}`,
      itemId,
      date: date.toISOString().split('T')[0],
      region: 'US-National',
      nominalPrice: Math.round(currentPrice * 100) / 100,
      unit: ITEMS.find(i => i.id === itemId)?.unitStandard || 'count',
      sourceId,
      confidence: 'high'
    })
    
    date = new Date(date.setMonth(date.getMonth() + 1))
  }
  
  return points
}

export const PRICE_DATA: PricePoint[] = [
  ...generatePriceHistory('eggs-dozen', 2.10, 0.05, 0.003, 'usda-1'),
  ...generatePriceHistory('milk-gallon', 3.50, 0.03, 0.002, 'usda-1'),
  ...generatePriceHistory('butter-lb', 4.20, 0.04, 0.0025, 'usda-1'),
  ...generatePriceHistory('cheese-lb', 5.80, 0.03, 0.002, 'usda-1'),
  ...generatePriceHistory('ground-beef-lb', 4.50, 0.04, 0.003, 'usda-1'),
  ...generatePriceHistory('tenderloin-lb', 18.00, 0.05, 0.0025, 'usda-1'),
  ...generatePriceHistory('gasoline-gallon', 3.20, 0.08, 0.002, 'eia-1'),
  ...generatePriceHistory('propane-gallon', 2.80, 0.06, 0.0015, 'eia-1')
]

function generateWageHistory(
  wageType: 'minimum' | 'median',
  baseWage: number,
  growth: number
): WageSeries[] {
  const points: WageSeries[] = []
  const startDate = new Date('2014-01-01')
  const endDate = new Date('2024-12-01')
  
  let currentWage = baseWage
  let date = new Date(startDate)
  
  while (date <= endDate) {
    currentWage = currentWage * (1 + growth)
    
    points.push({
      id: `${wageType}-${date.toISOString()}`,
      region: 'US-National',
      date: date.toISOString().split('T')[0],
      wageValue: Math.round(currentWage * 100) / 100,
      wageType,
      sourceId: 'bls-1',
      effectiveDate: date.toISOString().split('T')[0],
      jurisdiction: 'federal'
    })
    
    date = new Date(date.setMonth(date.getMonth() + 1))
  }
  
  return points
}

export const WAGE_DATA: WageSeries[] = [
  ...generateWageHistory('minimum', 7.25, 0.0002),
  ...generateWageHistory('median', 19.50, 0.002)
]

function generateCPIHistory(baseValue: number, baseYear: number, avgInflation: number): CPIDataPoint[] {
  const points: CPIDataPoint[] = []
  const startDate = new Date('2014-01-01')
  const endDate = new Date('2024-12-01')
  
  let date = new Date(startDate)
  const startYear = date.getFullYear()
  const yearDiff = startYear - baseYear
  
  let currentValue = baseValue * Math.pow(1 + avgInflation, yearDiff)
  
  while (date <= endDate) {
    const monthlyInflation = avgInflation / 12
    const seasonalVariation = (Math.random() - 0.5) * 0.001
    currentValue = currentValue * (1 + monthlyInflation + seasonalVariation)
    
    points.push({
      id: `cpi-${date.toISOString()}`,
      date: date.toISOString().split('T')[0],
      region: 'US-National',
      value: Math.round(currentValue * 1000) / 1000,
      baseYear: baseYear,
      sourceId: 'bls-cpi'
    })
    
    date = new Date(date.setMonth(date.getMonth() + 1))
  }
  
  return points
}

export const CPI_DATA: CPIDataPoint[] = generateCPIHistory(100, 1982, 0.025)

export function getCPIHistory(region: string = 'US-National'): CPIDataPoint[] {
  return CPI_DATA.filter(c => c.region === region)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
}

export function getCPIForDate(date: string, region: string = 'US-National'): CPIDataPoint | undefined {
  const history = getCPIHistory(region)
  return history.find(c => c.date === date) || history[history.length - 1]
}

export function getLatestCPI(region: string = 'US-National'): CPIDataPoint | undefined {
  const history = getCPIHistory(region)
  return history[history.length - 1]
}

export function getItemById(id: string): Item | undefined {
  return ITEMS.find(item => item.id === id)
}

export function getPriceHistory(itemId: string, region: string = 'US-National'): PricePoint[] {
  return PRICE_DATA.filter(p => p.itemId === itemId && p.region === region)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
}

export function getWageHistory(wageType: 'minimum' | 'median', region: string = 'US-National'): WageSeries[] {
  return WAGE_DATA.filter(w => w.wageType === wageType && w.region === region)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
}

export function getLatestPrice(itemId: string, region: string = 'US-National'): PricePoint | undefined {
  const history = getPriceHistory(itemId, region)
  return history[history.length - 1]
}

export function getLatestWage(wageType: 'minimum' | 'median', region: string = 'US-National'): WageSeries | undefined {
  const history = getWageHistory(wageType, region)
  return history[history.length - 1]
}

export function calculateHoursOfWork(price: number, hourlyWage: number): number {
  return Math.round((price / hourlyWage) * 100) / 100
}

export function calculatePriceChange(oldPrice: number, newPrice: number): number {
  return Math.round(((newPrice - oldPrice) / oldPrice) * 10000) / 100
}

export function calculateRealPrice(nominalPrice: number, cpiValue: number, baseYear: number = 1982): number {
  const baseCPI = 100
  const adjustedPrice = (nominalPrice / cpiValue) * baseCPI
  return Math.round(adjustedPrice * 100) / 100
}

export function calculateInflationRate(oldCPI: number, newCPI: number): number {
  return Math.round(((newCPI - oldCPI) / oldCPI) * 10000) / 100
}

export function getPriceWithCPI(itemId: string, region: string = 'US-National'): Array<PricePoint & { realPrice: number, cpiValue: number }> {
  const priceHistory = getPriceHistory(itemId, region)
  const cpiHistory = getCPIHistory(region)
  
  return priceHistory.map(price => {
    const cpi = cpiHistory.find(c => c.date === price.date) || cpiHistory[cpiHistory.length - 1]
    const realPrice = calculateRealPrice(price.nominalPrice, cpi.value)
    
    return {
      ...price,
      realPrice,
      cpiValue: cpi.value
    }
  })
}

export function detectWageIncreaseEvents(
  wageType: 'minimum' | 'median',
  region: string = 'US-National'
): WageIncreaseEvent[] {
  const history = getWageHistory(wageType, region)
  const events: WageIncreaseEvent[] = []
  
  for (let i = 1; i < history.length; i++) {
    const prev = history[i - 1]
    const curr = history[i]
    
    if (curr.wageValue > prev.wageValue) {
      const increase = curr.wageValue - prev.wageValue
      const increasePercent = (increase / prev.wageValue) * 100
      
      if (increasePercent > 1) {
        events.push({
          effectiveDate: curr.date,
          oldWage: prev.wageValue,
          newWage: curr.wageValue,
          increase: Math.round(increase * 100) / 100,
          increasePercent: Math.round(increasePercent * 100) / 100,
          region: curr.region,
          jurisdiction: curr.jurisdiction || 'federal'
        })
      }
    }
  }
  
  return events
}

export function calculateAffordabilityMetrics(
  itemId: string,
  dateT1: string,
  dateT2: string,
  wageT1: number,
  wageT2: number,
  region: string = 'US-National'
): AffordabilityMetrics | null {
  const priceHistory = getPriceHistory(itemId, region)
  const item = getItemById(itemId)
  
  if (!item) return null
  
  const priceT1 = priceHistory.find(p => p.date === dateT1)
  const priceT2 = priceHistory.find(p => p.date === dateT2)
  
  if (!priceT1 || !priceT2) return null
  
  const hoursT1 = calculateHoursOfWork(priceT1.nominalPrice, wageT1)
  const hoursT2 = calculateHoursOfWork(priceT2.nominalPrice, wageT2)
  
  const affordabilityRatio = hoursT2 / hoursT1
  const absoluteChange = hoursT2 - hoursT1
  const percentChange = ((affordabilityRatio - 1) * 100)
  
  const nominalGrowth = ((priceT2.nominalPrice / priceT1.nominalPrice) - 1) * 100
  const wageGrowth = ((wageT2 / wageT1) - 1) * 100
  const relativeOutpacing = nominalGrowth - wageGrowth
  
  return {
    itemId,
    itemName: item.name,
    hoursT1: Math.round(hoursT1 * 100) / 100,
    hoursT2: Math.round(hoursT2 * 100) / 100,
    affordabilityRatio: Math.round(affordabilityRatio * 1000) / 1000,
    absoluteChange: Math.round(absoluteChange * 100) / 100,
    percentChange: Math.round(percentChange * 100) / 100,
    nominalGrowth: Math.round(nominalGrowth * 100) / 100,
    wageGrowth: Math.round(wageGrowth * 100) / 100,
    relativeOutpacing: Math.round(relativeOutpacing * 100) / 100
  }
}

export function calculateBasketAffordabilityMetrics(
  basketItemIds: string[],
  dateT1: string,
  dateT2: string,
  wageT1: number,
  wageT2: number,
  region: string = 'US-National',
  verdictThreshold: number = 1.00
): BasketAffordabilityMetrics | null {
  let basketCostT1 = 0
  let basketCostT2 = 0
  let validItems = 0
  
  for (const itemId of basketItemIds) {
    const priceHistory = getPriceHistory(itemId, region)
    const priceT1 = priceHistory.find(p => p.date === dateT1)
    const priceT2 = priceHistory.find(p => p.date === dateT2)
    
    if (priceT1 && priceT2) {
      basketCostT1 += priceT1.nominalPrice
      basketCostT2 += priceT2.nominalPrice
      validItems++
    }
  }
  
  if (validItems === 0) return null
  
  const hoursT1 = calculateHoursOfWork(basketCostT1, wageT1)
  const hoursT2 = calculateHoursOfWork(basketCostT2, wageT2)
  
  const affordabilityRatio = hoursT2 / hoursT1
  const absoluteChange = hoursT2 - hoursT1
  const percentChange = ((affordabilityRatio - 1) * 100)
  
  const nominalGrowth = ((basketCostT2 / basketCostT1) - 1) * 100
  const wageGrowth = ((wageT2 / wageT1) - 1) * 100
  const relativeOutpacing = nominalGrowth - wageGrowth
  
  const coverageRatio = validItems / basketItemIds.length
  let confidenceLevel: 'high' | 'medium' | 'low' = 'high'
  if (coverageRatio < 0.7) confidenceLevel = 'low'
  else if (coverageRatio < 0.9) confidenceLevel = 'medium'
  
  let verdict: 'kept-up' | 'lagged' | 'unclear'
  if (confidenceLevel === 'low') {
    verdict = 'unclear'
  } else if (affordabilityRatio <= verdictThreshold) {
    verdict = 'kept-up'
  } else {
    verdict = 'lagged'
  }
  
  return {
    basketCostT1: Math.round(basketCostT1 * 100) / 100,
    basketCostT2: Math.round(basketCostT2 * 100) / 100,
    hoursT1: Math.round(hoursT1 * 100) / 100,
    hoursT2: Math.round(hoursT2 * 100) / 100,
    affordabilityRatio: Math.round(affordabilityRatio * 1000) / 1000,
    absoluteChange: Math.round(absoluteChange * 100) / 100,
    percentChange: Math.round(percentChange * 100) / 100,
    nominalGrowth: Math.round(nominalGrowth * 100) / 100,
    wageGrowth: Math.round(wageGrowth * 100) / 100,
    relativeOutpacing: Math.round(relativeOutpacing * 100) / 100,
    verdict,
    confidenceLevel
  }
}

export function calculateIndexedSeries(
  values: number[],
  baseIndex: number = 0
): number[] {
  if (values.length === 0 || baseIndex >= values.length) return []
  const baseValue = values[baseIndex]
  return values.map(v => (v / baseValue) * 100)
}

import type { WageIncreaseEvent, AffordabilityMetrics, BasketAffordabilityMetrics } from './types'
