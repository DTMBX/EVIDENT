import type { Source, DataConnector, QAFlag } from './types'

export type MonitoringAlertLevel = 'critical' | 'warning' | 'info'
export type MonitoringMetricType = 
  | 'api-availability' 
  | 'response-time' 
  | 'data-freshness' 
  | 'data-quality' 
  | 'error-rate'
  | 'rate-limit'

export interface APIHealthStatus {
  connectorId: string
  sourceId: string
  name: string
  status: 'healthy' | 'degraded' | 'offline' | 'maintenance'
  lastSuccessfulFetch?: string
  lastFailedFetch?: string
  consecutiveFailures: number
  uptime24h: number
  uptime7d: number
  responseTimeMs: number
  errorCount24h: number
  requestCount24h: number
  currentRateLimit: {
    used: number
    limit: number
    resetAt: string
  }
  circuitBreakerStatus: 'closed' | 'open' | 'half-open'
}

export interface DataQualityMetric {
  id: string
  sourceId: string
  itemId: string
  timestamp: string
  metricType: MonitoringMetricType
  value: number
  threshold: number
  status: 'pass' | 'warning' | 'fail'
  message: string
  details?: Record<string, unknown>
}

export interface MonitoringAlert {
  id: string
  level: MonitoringAlertLevel
  type: MonitoringMetricType
  sourceId: string
  connectorId: string
  title: string
  message: string
  timestamp: string
  acknowledgedAt?: string
  acknowledgedBy?: string
  resolvedAt?: string
  relatedMetrics: string[]
  actionItems: string[]
  affectedItems: string[]
  estimatedImpact: 'low' | 'medium' | 'high'
}

export interface APICallLog {
  id: string
  connectorId: string
  sourceId: string
  endpoint: string
  method: string
  timestamp: string
  responseTimeMs: number
  statusCode: number
  success: boolean
  errorMessage?: string
  requestPayload?: string
  responseSize?: number
  retryAttempt: number
}

export interface DataFreshnessStatus {
  sourceId: string
  itemId?: string
  lastDataPoint: string
  expectedFrequency: 'hourly' | 'daily' | 'weekly' | 'monthly'
  staleness: 'current' | 'recent' | 'stale' | 'very-stale'
  hoursStale: number
  nextExpectedUpdate: string
}

export interface QualityScorecard {
  sourceId: string
  period: '24h' | '7d' | '30d'
  scores: {
    availability: number
    freshness: number
    accuracy: number
    completeness: number
    consistency: number
    overall: number
  }
  trendDirection: 'improving' | 'stable' | 'degrading'
  flagCount: {
    error: number
    warning: number
    info: number
  }
  recommendations: string[]
}

export interface CircuitBreakerState {
  connectorId: string
  status: 'closed' | 'open' | 'half-open'
  failureCount: number
  threshold: number
  openedAt?: string
  nextRetryAt?: string
  halfOpenSuccesses: number
  halfOpenFailures: number
}

export interface RateLimitStatus {
  connectorId: string
  sourceId: string
  window: 'minute' | 'hour' | 'day'
  current: number
  limit: number
  percentUsed: number
  resetAt: string
  throttled: boolean
  queuedRequests: number
}

export interface SystemHealthSummary {
  timestamp: string
  overallStatus: 'healthy' | 'degraded' | 'critical'
  connectors: {
    total: number
    healthy: number
    degraded: number
    offline: number
  }
  alerts: {
    critical: number
    warning: number
    info: number
  }
  dataFreshness: {
    current: number
    stale: number
    veryStale: number
  }
  performance: {
    avgResponseTimeMs: number
    successRate: number
    errorRate: number
  }
  nextScheduledRefresh: string
}

export interface AlertRule {
  id: string
  name: string
  enabled: boolean
  metricType: MonitoringMetricType
  condition: 'above' | 'below' | 'equals'
  threshold: number
  duration: number
  level: MonitoringAlertLevel
  sourceIds: string[]
  notificationChannels: ('ui' | 'console' | 'persist')[]
  cooldownMinutes: number
  lastTriggered?: string
}

export interface MonitoringDashboardConfig {
  refreshIntervalSeconds: number
  alertRetentionDays: number
  logRetentionDays: number
  enableNotifications: boolean
  alertRules: AlertRule[]
  thresholds: {
    responseTimeWarningMs: number
    responseTimeCriticalMs: number
    errorRateWarning: number
    errorRateCritical: number
    dataFreshnessWarningHours: number
    dataFreshnessCriticalHours: number
    uptimeWarning: number
    uptimeCritical: number
  }
}

export const DEFAULT_MONITORING_CONFIG: MonitoringDashboardConfig = {
  refreshIntervalSeconds: 30,
  alertRetentionDays: 30,
  logRetentionDays: 7,
  enableNotifications: true,
  alertRules: [
    {
      id: 'high-error-rate',
      name: 'High Error Rate',
      enabled: true,
      metricType: 'error-rate',
      condition: 'above',
      threshold: 0.25,
      duration: 300,
      level: 'critical',
      sourceIds: [],
      notificationChannels: ['ui', 'persist'],
      cooldownMinutes: 15,
    },
    {
      id: 'api-offline',
      name: 'API Offline',
      enabled: true,
      metricType: 'api-availability',
      condition: 'equals',
      threshold: 0,
      duration: 180,
      level: 'critical',
      sourceIds: [],
      notificationChannels: ['ui', 'persist'],
      cooldownMinutes: 10,
    },
    {
      id: 'stale-data',
      name: 'Stale Data',
      enabled: true,
      metricType: 'data-freshness',
      condition: 'above',
      threshold: 48,
      duration: 0,
      level: 'warning',
      sourceIds: [],
      notificationChannels: ['ui', 'persist'],
      cooldownMinutes: 60,
    },
    {
      id: 'slow-response',
      name: 'Slow Response Time',
      enabled: true,
      metricType: 'response-time',
      condition: 'above',
      threshold: 5000,
      duration: 300,
      level: 'warning',
      sourceIds: [],
      notificationChannels: ['ui'],
      cooldownMinutes: 30,
    },
  ],
  thresholds: {
    responseTimeWarningMs: 3000,
    responseTimeCriticalMs: 10000,
    errorRateWarning: 0.15,
    errorRateCritical: 0.30,
    dataFreshnessWarningHours: 48,
    dataFreshnessCriticalHours: 168,
    uptimeWarning: 0.95,
    uptimeCritical: 0.85,
  },
}

export function calculateStaleness(
  lastDataPoint: string,
  expectedFrequency: 'hourly' | 'daily' | 'weekly' | 'monthly'
): { staleness: 'current' | 'recent' | 'stale' | 'very-stale'; hoursStale: number } {
  const now = new Date()
  const lastPoint = new Date(lastDataPoint)
  const hoursStale = (now.getTime() - lastPoint.getTime()) / (1000 * 60 * 60)

  const thresholds = {
    hourly: { recent: 2, stale: 12, veryStale: 48 },
    daily: { recent: 36, stale: 72, veryStale: 168 },
    weekly: { recent: 240, stale: 504, veryStale: 1008 },
    monthly: { recent: 1080, stale: 2160, veryStale: 4320 },
  }

  const t = thresholds[expectedFrequency]

  if (hoursStale <= t.recent) return { staleness: 'current', hoursStale }
  if (hoursStale <= t.stale) return { staleness: 'recent', hoursStale }
  if (hoursStale <= t.veryStale) return { staleness: 'stale', hoursStale }
  return { staleness: 'very-stale', hoursStale }
}

export function calculateQualityScore(metrics: {
  totalRequests: number
  successfulRequests: number
  avgResponseTime: number
  dataPointsCurrent: number
  dataPointsTotal: number
  errorFlags: number
  warningFlags: number
}): number {
  const availabilityScore = metrics.totalRequests > 0
    ? (metrics.successfulRequests / metrics.totalRequests) * 100
    : 0

  const performanceScore = Math.max(0, 100 - (metrics.avgResponseTime / 100))

  const freshnessScore = metrics.dataPointsTotal > 0
    ? (metrics.dataPointsCurrent / metrics.dataPointsTotal) * 100
    : 0

  const qualityPenalty = (metrics.errorFlags * 5) + (metrics.warningFlags * 2)
  const qualityScore = Math.max(0, 100 - qualityPenalty)

  const overallScore = (
    availabilityScore * 0.35 +
    performanceScore * 0.20 +
    freshnessScore * 0.25 +
    qualityScore * 0.20
  )

  return Math.round(overallScore)
}

export function evaluateAlertRule(
  rule: AlertRule,
  currentValue: number,
  durationSeconds: number
): boolean {
  if (!rule.enabled) return false
  if (durationSeconds < rule.duration) return false

  switch (rule.condition) {
    case 'above':
      return currentValue > rule.threshold
    case 'below':
      return currentValue < rule.threshold
    case 'equals':
      return currentValue === rule.threshold
    default:
      return false
  }
}

export function getHealthStatusFromUptime(uptime: number): 'healthy' | 'degraded' | 'offline' {
  if (uptime >= 0.95) return 'healthy'
  if (uptime >= 0.80) return 'degraded'
  return 'offline'
}

export function getAlertPriority(level: MonitoringAlertLevel): number {
  switch (level) {
    case 'critical':
      return 1
    case 'warning':
      return 2
    case 'info':
      return 3
    default:
      return 999
  }
}

export function formatStaleness(hoursStale: number): string {
  if (hoursStale < 1) return `${Math.round(hoursStale * 60)} minutes`
  if (hoursStale < 48) return `${Math.round(hoursStale)} hours`
  const days = Math.round(hoursStale / 24)
  return `${days} day${days !== 1 ? 's' : ''}`
}
