import type {
  DataConnector,
  FetchSeriesRequest,
  FetchSeriesResponse,
  RawPricePoint,
  QAFlag,
  NormalizedPricePoint,
  ValidationResult,
  NormalizationPipeline,
  UnitStandard,
  ConfidenceScore,
} from './types'
import { EXPANDED_ITEMS, EXPANDED_SOURCES, convertUnit } from './expanded-catalog'
import { blsClient, eiaClient, usdaClient } from './api-clients'

export const DATA_CONNECTORS: DataConnector[] = [
  {
    id: 'usda-ams-connector',
    sourceId: 'usda-ams',
    name: 'USDA AMS Dairy & Protein Connector',
    enabled: true,
    featureFlag: 'connector-usda-ams',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 1000,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 60,
      requestsPerHour: 1000,
    },
    allowedDomains: ['ams.usda.gov', 'marketnews.usda.gov'],
  },
  {
    id: 'usda-nass-connector',
    sourceId: 'usda-nass',
    name: 'USDA NASS Agricultural Statistics Connector',
    enabled: true,
    featureFlag: 'connector-usda-nass',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 1000,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 60,
      requestsPerHour: 1000,
    },
    allowedDomains: ['nass.usda.gov', 'quickstats.nass.usda.gov'],
  },
  {
    id: 'eia-petroleum-connector',
    sourceId: 'eia-petroleum',
    name: 'EIA Petroleum Marketing Connector',
    enabled: true,
    featureFlag: 'connector-eia-petroleum',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 1500,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 100,
      requestsPerHour: 5000,
    },
    allowedDomains: ['eia.gov', 'api.eia.gov'],
  },
  {
    id: 'eia-natural-gas-connector',
    sourceId: 'eia-natural-gas',
    name: 'EIA Natural Gas Navigator Connector',
    enabled: true,
    featureFlag: 'connector-eia-gas',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 1500,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 100,
      requestsPerHour: 5000,
    },
    allowedDomains: ['eia.gov', 'api.eia.gov'],
  },
  {
    id: 'eia-electricity-connector',
    sourceId: 'eia-electricity',
    name: 'EIA Electric Power Monthly Connector',
    enabled: true,
    featureFlag: 'connector-eia-electricity',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 1500,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 100,
      requestsPerHour: 5000,
    },
    allowedDomains: ['eia.gov', 'api.eia.gov'],
  },
  {
    id: 'bls-wage-connector',
    sourceId: 'bls-wage',
    name: 'BLS Wage Data Connector',
    enabled: true,
    featureFlag: 'connector-bls-wage',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 2000,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 25,
      requestsPerHour: 500,
    },
    allowedDomains: ['bls.gov', 'api.bls.gov'],
  },
  {
    id: 'bls-cpi-connector',
    sourceId: 'bls-cpi',
    name: 'BLS Consumer Price Index Connector',
    enabled: true,
    featureFlag: 'connector-bls-cpi',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 2000,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 25,
      requestsPerHour: 500,
    },
    allowedDomains: ['bls.gov', 'api.bls.gov'],
  },
  {
    id: 'fred-housing-connector',
    sourceId: 'fred-housing',
    name: 'FRED Housing Data Connector',
    enabled: true,
    featureFlag: 'connector-fred-housing',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 1000,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 120,
      requestsPerHour: 10000,
    },
    allowedDomains: ['fred.stlouisfed.org', 'api.stlouisfed.org'],
  },
]

export async function fetchSeries(
  connector: DataConnector,
  request: FetchSeriesRequest
): Promise<FetchSeriesResponse> {
  const response: FetchSeriesResponse = {
    rawPoints: [],
    metadata: {
      sourceId: connector.sourceId,
      fetchTimestamp: new Date().toISOString(),
      recordCount: 0,
      coverage: 0,
      errors: [],
      warnings: [],
    },
  }

  if (!connector.enabled) {
    response.metadata.errors.push('Connector is disabled')
    return response
  }

  try {
    const rawPoints = await fetchRealData(connector, request)
    response.rawPoints = rawPoints
    response.metadata.recordCount = rawPoints.length
    response.metadata.coverage = calculateCoverage(rawPoints, request.dateRange)
    
    if (rawPoints.length === 0) {
      response.metadata.warnings.push('No data returned from API - falling back to simulated data')
      const simulatedPoints = await simulateFetch(connector, request)
      response.rawPoints = simulatedPoints
      response.metadata.recordCount = simulatedPoints.length
      response.metadata.coverage = calculateCoverage(simulatedPoints, request.dateRange)
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    response.metadata.errors.push(errorMessage)
    response.metadata.warnings.push('Falling back to simulated data due to API error')
    
    try {
      const simulatedPoints = await simulateFetch(connector, request)
      response.rawPoints = simulatedPoints
      response.metadata.recordCount = simulatedPoints.length
      response.metadata.coverage = calculateCoverage(simulatedPoints, request.dateRange)
    } catch (fallbackError) {
      response.metadata.errors.push('Fallback to simulated data also failed')
    }
  }

  return response
}

async function fetchRealData(
  connector: DataConnector,
  request: FetchSeriesRequest
): Promise<RawPricePoint[]> {
  const item = EXPANDED_ITEMS.find(i => i.id === request.itemId)
  if (!item) {
    throw new Error(`Item ${request.itemId} not found`)
  }

  if (!item.sourceSeriesIds.includes(connector.sourceId)) {
    throw new Error(`Source ${connector.sourceId} does not provide data for item ${request.itemId}`)
  }

  const startYear = new Date(request.dateRange.start).getFullYear().toString()
  const endYear = new Date(request.dateRange.end).getFullYear().toString()

  switch (connector.sourceId) {
    case 'bls-cpi':
      return blsClient.fetchSeries({
        seriesId: getBLSSeriesId(request.itemId, request.region),
        startYear,
        endYear,
        region: request.region,
      })

    case 'bls-wage':
      return blsClient.fetchSeries({
        seriesId: getBLSWageSeriesId(request.region),
        startYear,
        endYear,
        region: request.region,
      })

    case 'eia-petroleum':
      return eiaClient.fetchSeries({
        seriesId: getEIAPetroleumSeriesId(request.itemId),
        startDate: request.dateRange.start,
        endDate: request.dateRange.end,
      })

    case 'eia-natural-gas':
      return eiaClient.fetchSeries({
        seriesId: getEIANaturalGasSeriesId(request.itemId),
        startDate: request.dateRange.start,
        endDate: request.dateRange.end,
      })

    case 'eia-electricity':
      return eiaClient.fetchSeries({
        seriesId: getEIAElectricitySeriesId(request.itemId),
        startDate: request.dateRange.start,
        endDate: request.dateRange.end,
      })

    case 'usda-nass':
      return usdaClient.fetchQuickStats({
        commodity: getUSDAcommodity(request.itemId),
        dataItem: 'PRICE RECEIVED',
        domain: 'TOTAL',
        beginDate: request.dateRange.start,
        endDate: request.dateRange.end,
      })

    default:
      throw new Error(`Unsupported connector: ${connector.sourceId}`)
  }
}

function getBLSSeriesId(itemId: string, region: string): string {
  const cpiSeriesMap: Record<string, string> = {
    'cpi-all-items': 'CUUR0000SA0',
    'cpi-food': 'CUUR0000SAF',
    'cpi-energy': 'CUUR0000SA0E',
  }
  return cpiSeriesMap[itemId] || 'CUUR0000SA0'
}

function getBLSWageSeriesId(region: string): string {
  return 'CES0000000003'
}

function getEIAPetroleumSeriesId(itemId: string): string {
  const seriesMap: Record<string, string> = {
    'gasoline-gallon': 'PET.EMM_EPM0_PTE_NUS_DPG.M',
    'diesel-gallon': 'PET.EMD_EPD2D_PTE_NUS_DPG.M',
    'heating-oil-gallon': 'PET.EMM_EPMRR_PTE_NUS_DPG.M',
    'propane-gallon': 'PET.EER_EPPLLPA_PF4_Y35NY_DPG.M',
  }
  return seriesMap[itemId] || 'PET.EMM_EPM0_PTE_NUS_DPG.M'
}

function getEIANaturalGasSeriesId(itemId: string): string {
  return 'NG.N3020US3.M'
}

function getEIAElectricitySeriesId(itemId: string): string {
  return 'ELEC.PRICE.US-ALL.M'
}

function getUSDAcommodity(itemId: string): string {
  const commodityMap: Record<string, string> = {
    'milk-gallon': 'MILK',
    'eggs-dozen': 'EGGS',
    'butter-lb': 'BUTTER',
    'cheese-lb': 'CHEESE',
    'ground-beef-lb': 'CATTLE',
    'pork-chops-lb': 'HOGS',
    'chicken-breast-lb': 'BROILERS',
    'apples-lb': 'APPLES',
    'potatoes-lb': 'POTATOES',
    'tomatoes-lb': 'TOMATOES',
  }
  return commodityMap[itemId] || 'MILK'
}

async function simulateFetch(
  connector: DataConnector,
  request: FetchSeriesRequest
): Promise<RawPricePoint[]> {
  await new Promise(resolve => setTimeout(resolve, 500))

  const item = EXPANDED_ITEMS.find(i => i.id === request.itemId)
  if (!item) {
    throw new Error(`Item ${request.itemId} not found`)
  }

  if (!item.sourceSeriesIds.includes(connector.sourceId)) {
    throw new Error(`Source ${connector.sourceId} does not provide data for item ${request.itemId}`)
  }

  const points: RawPricePoint[] = []
  const startDate = new Date(request.dateRange.start)
  const endDate = new Date(request.dateRange.end)
  
  let currentDate = new Date(startDate)
  let basePrice = getBasePrice(request.itemId)
  
  while (currentDate <= endDate) {
    const randomVariation = (Math.random() - 0.5) * 0.1
    const trendGrowth = 0.003
    basePrice = basePrice * (1 + randomVariation + trendGrowth)
    
    points.push({
      id: `${request.itemId}-${currentDate.toISOString()}-raw`,
      itemId: request.itemId,
      date: currentDate.toISOString().split('T')[0],
      region: request.region,
      value: Math.round(basePrice * 100) / 100,
      unit: item.unitStandard,
      sourceId: connector.sourceId,
      retrievalTimestamp: new Date().toISOString(),
      sourceUrl: EXPANDED_SOURCES.find(s => s.id === connector.sourceId)?.url || '',
      checksumHash: generateChecksum(request.itemId, currentDate.toISOString()),
    })
    
    currentDate.setMonth(currentDate.getMonth() + 1)
  }
  
  return points
}

function getBasePrice(itemId: string): number {
  const basePrices: Record<string, number> = {
    'eggs-dozen': 2.10,
    'milk-gallon': 3.50,
    'butter-lb': 4.20,
    'cheese-lb': 5.80,
    'bread-loaf': 2.50,
    'rice-lb': 1.20,
    'pasta-lb': 1.50,
    'flour-lb': 0.60,
    'sugar-lb': 0.70,
    'salt-lb': 0.50,
    'coffee-lb': 6.50,
    'chicken-breast-lb': 4.50,
    'whole-chicken-lb': 1.80,
    'ground-beef-lb': 4.50,
    'beef-steak-lb': 11.00,
    'pork-chops-lb': 4.00,
    'bacon-lb': 6.20,
    'tuna-canned-oz': 1.20,
    'beans-dry-lb': 1.30,
    'apples-lb': 1.80,
    'bananas-lb': 0.60,
    'potatoes-lb': 0.80,
    'onions-lb': 1.20,
    'tomatoes-lb': 2.00,
    'lettuce-head': 1.50,
    'toilet-paper-roll': 0.80,
    'paper-towels-roll': 1.20,
    'detergent-oz': 0.15,
    'soap-bar': 1.50,
    'diapers-count': 0.30,
    'gasoline-gallon': 3.20,
    'diesel-gallon': 3.50,
    'propane-gallon': 2.80,
    'heating-oil-gallon': 3.80,
    'electricity-kWh': 0.14,
    'natural-gas-therm': 1.20,
    'rent-index': 300.00,
    'seeds-packet': 3.50,
    'potting-soil-lb': 0.40,
    'fertilizer-lb': 0.90,
    'feed-animal-lb': 0.35,
  }
  
  return basePrices[itemId] || 10.00
}

function calculateCoverage(points: RawPricePoint[], dateRange: { start: string; end: string }): number {
  if (points.length === 0) return 0
  
  const startDate = new Date(dateRange.start)
  const endDate = new Date(dateRange.end)
  const totalMonths = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24 * 30))
  
  return Math.min(100, (points.length / totalMonths) * 100)
}

function generateChecksum(itemId: string, date: string): string {
  const data = `${itemId}-${date}`
  let hash = 0
  for (let i = 0; i < data.length; i++) {
    const char = data.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash).toString(16)
}

export function validateRawData(rawPoints: RawPricePoint[]): ValidationResult {
  const errors: QAFlag[] = []
  const warnings: QAFlag[] = []
  let validPoints = 0
  
  rawPoints.forEach((point, index) => {
    let isValid = true
    
    if (!point.id || !point.itemId || !point.date) {
      errors.push({
        type: 'schema-error',
        severity: 'error',
        message: `Point at index ${index} missing required fields`,
        detectedAt: new Date().toISOString(),
      })
      isValid = false
    }
    
    if (point.value < 0) {
      errors.push({
        type: 'negative-value',
        severity: 'error',
        message: `Negative price ${point.value} for ${point.itemId} on ${point.date}`,
        detectedAt: new Date().toISOString(),
      })
      isValid = false
    }
    
    const item = EXPANDED_ITEMS.find(i => i.id === point.itemId)
    if (item && point.unit !== item.unitStandard) {
      if (!item.acceptableAlternateUnits.includes(point.unit as UnitStandard)) {
        warnings.push({
          type: 'unit-mismatch',
          severity: 'warning',
          message: `Unit ${point.unit} for ${point.itemId} does not match standard ${item.unitStandard}`,
          detectedAt: new Date().toISOString(),
        })
      }
    }
    
    if (index > 0) {
      const prevPoint = rawPoints[index - 1]
      if (prevPoint.itemId === point.itemId) {
        const pctChange = Math.abs((point.value - prevPoint.value) / prevPoint.value)
        if (pctChange > 0.50) {
          warnings.push({
            type: 'sudden-jump',
            severity: 'warning',
            message: `Sudden ${(pctChange * 100).toFixed(1)}% change for ${point.itemId} from ${prevPoint.date} to ${point.date}`,
            detectedAt: new Date().toISOString(),
          })
        }
      }
    }
    
    if (isValid) validPoints++
  })
  
  const duplicates = findDuplicates(rawPoints)
  duplicates.forEach(dup => {
    errors.push({
      type: 'duplicate',
      severity: 'error',
      message: `Duplicate entry for ${dup.itemId} on ${dup.date}`,
      detectedAt: new Date().toISOString(),
    })
  })
  
  const coverage = rawPoints.length > 0 ? (validPoints / rawPoints.length) * 100 : 0
  
  return {
    passed: errors.length === 0,
    errors,
    warnings,
    stats: {
      totalPoints: rawPoints.length,
      validPoints,
      flaggedPoints: errors.length + warnings.length,
      coverage,
    },
  }
}

function findDuplicates(points: RawPricePoint[]): RawPricePoint[] {
  const seen = new Set<string>()
  const duplicates: RawPricePoint[] = []
  
  points.forEach(point => {
    const key = `${point.itemId}-${point.date}-${point.region}`
    if (seen.has(key)) {
      duplicates.push(point)
    } else {
      seen.add(key)
    }
  })
  
  return duplicates
}

export function normalizePriceData(
  rawPoints: RawPricePoint[],
  validationResult: ValidationResult
): NormalizationPipeline {
  const normalizedData: NormalizedPricePoint[] = []
  
  rawPoints.forEach((raw, index) => {
    if (validationResult.errors.some(e => e.message.includes(`index ${index}`))) {
      return
    }
    
    const item = EXPANDED_ITEMS.find(i => i.id === raw.itemId)
    if (!item) return
    
    let normalizedValue = raw.value
    let normalizedUnit = raw.unit as UnitStandard
    
    if (raw.unit !== item.unitStandard) {
      try {
        normalizedValue = convertUnit(raw.value, raw.unit as UnitStandard, item.unitStandard)
        normalizedUnit = item.unitStandard
      } catch (error) {
        return
      }
    }
    
    const qaFlags: QAFlag[] = validationResult.warnings.filter(
      w => w.message.includes(raw.itemId) && w.message.includes(raw.date)
    )
    
    const confidence = determineConfidence(qaFlags, raw)
    
    normalizedData.push({
      id: `${raw.id}-normalized`,
      rawId: raw.id,
      itemId: raw.itemId,
      date: raw.date,
      region: raw.region,
      normalizedValue,
      normalizedUnit,
      frequency: 'monthly',
      aggregationMethod: 'end-of-period',
      qaFlags,
      confidence,
      version: 1,
    })
  })
  
  return {
    rawData: rawPoints,
    normalizedData,
    validationResult,
    processingTimestamp: new Date().toISOString(),
    version: 1,
  }
}

function determineConfidence(qaFlags: QAFlag[], raw: RawPricePoint): 'high' | 'medium' | 'low' {
  const errorCount = qaFlags.filter(f => f.severity === 'error').length
  const warningCount = qaFlags.filter(f => f.severity === 'warning').length
  
  if (errorCount > 0) return 'low'
  if (warningCount > 1) return 'medium'
  return 'high'
}

export function computeConfidenceScore(
  seriesId: string,
  normalizedPoints: NormalizedPricePoint[],
  source: { reliabilityTier: 'tier-1' | 'tier-2' | 'tier-3' }
): ConfidenceScore {
  const now = new Date()
  const latestPoint = normalizedPoints[normalizedPoints.length - 1]
  const latestDate = latestPoint ? new Date(latestPoint.date) : new Date(0)
  const daysSinceUpdate = (now.getTime() - latestDate.getTime()) / (1000 * 60 * 60 * 24)
  
  const recency = Math.max(0, 100 - (daysSinceUpdate / 30) * 50)
  
  const totalPoints = normalizedPoints.length
  const expectedPoints = 120
  const coverage = Math.min(100, (totalPoints / expectedPoints) * 100)
  
  const flaggedPoints = normalizedPoints.filter(p => p.qaFlags.length > 0).length
  const outlierRate = totalPoints > 0 ? (flaggedPoints / totalPoints) * 100 : 0
  const outlierScore = Math.max(0, 100 - outlierRate * 2)
  
  const tierScores = { 'tier-1': 100, 'tier-2': 75, 'tier-3': 50 }
  const providerTier = tierScores[source.reliabilityTier]
  
  const score = (coverage * 0.3 + recency * 0.2 + outlierScore * 0.3 + providerTier * 0.2)
  
  return {
    seriesId,
    score: Math.round(score * 10) / 10,
    factors: {
      coverage: Math.round(coverage * 10) / 10,
      recency: Math.round(recency * 10) / 10,
      outlierRate: Math.round(outlierRate * 10) / 10,
      providerTier,
    },
    computedAt: new Date().toISOString(),
  }
}

export function detectOutliers(points: NormalizedPricePoint[]): NormalizedPricePoint[] {
  if (points.length < 5) return points
  
  const values = points.map(p => p.normalizedValue)
  const median = calculateMedian(values)
  const deviations = values.map(v => Math.abs(v - median))
  const mad = calculateMedian(deviations)
  
  const threshold = 3.5
  
  return points.map((point, index) => {
    const deviation = Math.abs(point.normalizedValue - median)
    const robustZScore = mad > 0 ? deviation / (1.4826 * mad) : 0
    
    if (robustZScore > threshold) {
      const outlierFlag: QAFlag = {
        type: 'outlier',
        severity: 'warning',
        message: `Statistical outlier detected (robust z-score: ${robustZScore.toFixed(2)})`,
        detectedAt: new Date().toISOString(),
      }
      
      return {
        ...point,
        qaFlags: [...point.qaFlags, outlierFlag],
        confidence: 'low',
      }
    }
    
    return point
  })
}

function calculateMedian(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2
  } else {
    return sorted[mid]
  }
}
