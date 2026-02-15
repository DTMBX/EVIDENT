export type ItemCategory = 
  | 'dairy' 
  | 'meat' 
  | 'produce' 
  | 'grains' 
  | 'staples'
  | 'household' 
  | 'fuel' 
  | 'utilities'
  | 'proteins'
  | 'inputs'

export type UnitStandard = 
  | 'dozen' 
  | 'gallon' 
  | 'lb' 
  | 'oz'
  | 'kg'
  | 'liter'
  | 'count'
  | 'pack'
  | 'roll'
  | 'kWh'
  | 'therm'
  | 'ccf'
  | 'bushel'

export interface UnitConversion {
  fromUnit: UnitStandard
  toUnit: UnitStandard
  factor: number
}

export interface Item {
  id: string
  name: string
  category: ItemCategory
  unitStandard: UnitStandard
  acceptableAlternateUnits: UnitStandard[]
  conversions: UnitConversion[]
  description?: string
  synonyms?: string[]
  sourceSeriesIds: string[]
  regionCoverage: string[]
}

export interface RawPricePoint {
  id: string
  itemId: string
  date: string
  region: string
  value: number
  unit: UnitStandard
  sourceId: string
  retrievalTimestamp: string
  sourceUrl: string
  rawPayload?: string
  checksumHash?: string
}

export interface QAFlag {
  type: 'schema-error' | 'unit-mismatch' | 'negative-value' | 'outlier' | 'sudden-jump' | 'duplicate' | 'missing-interval' | 'revision' | 'interpolated'
  severity: 'error' | 'warning' | 'info'
  message: string
  detectedAt: string
}

export interface NormalizedPricePoint {
  id: string
  rawId: string
  itemId: string
  date: string
  region: string
  normalizedValue: number
  normalizedUnit: UnitStandard
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual'
  aggregationMethod?: 'end-of-period' | 'mean' | 'median'
  qaFlags: QAFlag[]
  confidence: 'high' | 'medium' | 'low'
  version: number
}

export interface PricePoint {
  id: string
  itemId: string
  date: string
  region: string
  nominalPrice: number
  unit: UnitStandard
  sourceId: string
  confidence: 'high' | 'medium' | 'low'
  realPrice?: number
  cpiValue?: number
  qaFlags?: QAFlag[]
  normalized?: NormalizedPricePoint
  raw?: RawPricePoint
}

export interface WageSeries {
  id: string
  region: string
  date: string
  wageValue: number
  wageType: 'minimum' | 'median' | 'sector' | 'user'
  sourceId?: string
  effectiveDate?: string
  jurisdiction?: 'federal' | 'state' | 'city'
}

export interface CPIDataPoint {
  id: string
  date: string
  region: string
  value: number
  baseYear: number
  sourceId: string
}

export interface Source {
  id: string
  name: string
  provider: string
  license: string
  terms: string
  url: string
  retrievalTimestamp: string
  isOfficial: boolean
  reliabilityTier: 'tier-1' | 'tier-2' | 'tier-3'
  refreshSchedule: RefreshSchedule
  coverageMap: Record<string, string[]>
  seriesIdentifiers: string[]
  status: 'active' | 'deprecated' | 'maintenance'
  lastSuccessfulFetch?: string
  lastError?: string
}

export interface DataConnector {
  id: string
  sourceId: string
  name: string
  enabled: boolean
  featureFlag: string
  retryConfig: {
    maxRetries: number
    backoffMs: number
    circuitBreakerThreshold: number
  }
  rateLimit: {
    requestsPerMinute: number
    requestsPerHour: number
  }
  allowedDomains: string[]
}

export interface FetchSeriesRequest {
  region: string
  itemId: string
  dateRange: {
    start: string
    end: string
  }
}

export interface FetchSeriesResponse {
  rawPoints: RawPricePoint[]
  metadata: {
    sourceId: string
    fetchTimestamp: string
    recordCount: number
    coverage: number
    errors: string[]
    warnings: string[]
  }
}

export interface Basket {
  id: string
  name: string
  items: Array<{
    itemId: string
    quantity: number
  }>
}

export interface UserWageConfig {
  type: 'manual' | 'sourced'
  hourlyWage?: number
  sourcedSeriesId?: string
  region: string
}

export type MetricMode = 'nominal' | 'real' | 'hours-of-work'

export interface ComparisonConfig {
  itemIds: string[]
  dateRange: {
    start: string
    end: string
  }
  metricMode: MetricMode
  region: string
}

export interface WageIncreaseEvent {
  effectiveDate: string
  oldWage: number
  newWage: number
  increase: number
  increasePercent: number
  region: string
  jurisdiction: 'federal' | 'state' | 'city'
}

export interface AffordabilityMetrics {
  itemId: string
  itemName: string
  hoursT1: number
  hoursT2: number
  affordabilityRatio: number
  absoluteChange: number
  percentChange: number
  nominalGrowth: number
  wageGrowth: number
  relativeOutpacing: number
}

export interface BasketAffordabilityMetrics {
  basketCostT1: number
  basketCostT2: number
  hoursT1: number
  hoursT2: number
  affordabilityRatio: number
  absoluteChange: number
  percentChange: number
  nominalGrowth: number
  wageGrowth: number
  relativeOutpacing: number
  verdict: 'kept-up' | 'lagged' | 'unclear'
  confidenceLevel: 'high' | 'medium' | 'low'
}

export interface AnalyticsConfig {
  region: string
  dateRange: {
    start: string
    end: string
  }
  baseDate: string
  wageType: 'minimum' | 'median'
  basketItemIds: string[]
  metricMode: MetricMode
  verdictThreshold: number
  eventWindowMonths: number
}

export type RefreshSchedule = 'manual' | 'hourly' | 'daily' | 'disabled'

export interface RefreshScheduleConfig {
  enabled: boolean
  schedule: RefreshSchedule
  lastScheduledRefresh?: string
  nextScheduledRefresh?: string
  autoRefreshEnabled: boolean
}

export interface SourceRefreshSchedule {
  sourceId: string
  schedule: RefreshSchedule
  enabled: boolean
}

export type Generation = 'silent' | 'boomer' | 'genx' | 'millennial' | 'genz'

export interface GenerationDefinition {
  id: Generation
  name: string
  birthYearStart: number
  birthYearEnd: number
  description: string
  color: string
}

export interface VolatilityMetrics {
  date: string
  value: number
  volatilityWindow: 3 | 5 | 10
  metric: 'price' | 'wage' | 'basket' | 'cpi'
  itemId?: string
}

export interface EconomicEvent {
  id: string
  name: string
  date: string
  endDate?: string
  type: 'recession' | 'policy' | 'shock' | 'crisis' | 'other'
  description: string
  citation: string
  citationUrl: string
  source: string
}

export interface AffordabilityByAge {
  generation: Generation
  birthYear: number
  age: number
  calendarYear: number
  basketHours: number
  wage: number
  basketCost: number
  interpolated: boolean
}

export interface DialoguePrompt {
  id: string
  category: 'affordability' | 'volatility' | 'wages' | 'general'
  question: string
  context: string
  relatedChartIds: string[]
  educatorNotes?: string
}

export interface DataGuardrails {
  chartId: string
  whatDataShows: string[]
  whatDataDoesNotShow: string[]
  assumptions: string[]
  limitations: string[]
  interpretivePerspectives?: Array<{
    label: string
    content: string
    isOpinion: boolean
  }>
}

export interface VolatilityConfig {
  enabled: boolean
  window: 3 | 5 | 10
  showBands: boolean
  smoothingMethod: 'none' | 'moving-average' | 'exponential'
}

export interface GenerationalConfig {
  selectedGenerations: Generation[]
  compareMode: 'timeline' | 'life-stage' | 'calendar-year'
  lifeStages: number[]
  showVolatility: boolean
  showEvents: boolean
}

export interface DecadeComparison {
  decade: string
  startYear: number
  endYear: number
  medianWage: number
  basketCost: number
  basketHours: number
  cpiAverage: number
  volatilityAverage: number
  coverage: number
}

export interface EconomicLearningModule {
  id: string
  title: string
  category: 'cycles' | 'inflation' | 'monetary-policy' | 'supply-shocks' | 'media'
  content: string
  readingLevel: number
  citations: Array<{
    text: string
    url: string
    source: string
  }>
  relatedTerms: string[]
  visualAid?: string
}

export interface DataRevision {
  id: string
  sourceId: string
  itemId: string
  revisionDate: string
  affectedDateRange: {
    start: string
    end: string
  }
  changes: Array<{
    date: string
    oldValue: number
    newValue: number
    reason?: string
  }>
  snapshotVersion: number
  retrievalTimestamp: string
}

export interface ConfidenceScore {
  seriesId: string
  score: number
  factors: {
    coverage: number
    recency: number
    outlierRate: number
    providerTier: number
  }
  computedAt: string
}

export interface SourceRegistry {
  sources: Source[]
  connectors: DataConnector[]
  lastUpdated: string
  version: string
}

export interface ValidationResult {
  passed: boolean
  errors: QAFlag[]
  warnings: QAFlag[]
  stats: {
    totalPoints: number
    validPoints: number
    flaggedPoints: number
    coverage: number
  }
}

export interface NormalizationPipeline {
  rawData: RawPricePoint[]
  normalizedData: NormalizedPricePoint[]
  validationResult: ValidationResult
  processingTimestamp: string
  version: number
}

export interface UserRole {
  userId: string
  role: 'anonymous' | 'registered' | 'analyst' | 'admin'
  permissions: string[]
  grantedAt: string
}

export interface AuditLog {
  id: string
  userId: string
  action: string
  resource: string
  timestamp: string
  metadata: Record<string, unknown>
  ipAddress?: string
}

export interface BasketTemplate {
  id: string
  name: string
  description: string
  category: 'family-4' | 'single-adult' | 'tradesperson' | 'custom'
  items: Array<{
    itemId: string
    quantity: number
  }>
  createdBy?: string
  isPublic: boolean
}
