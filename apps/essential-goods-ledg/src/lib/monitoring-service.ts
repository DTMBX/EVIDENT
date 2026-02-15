import type {
  APIHealthStatus,
  MonitoringAlert,
  APICallLog,
  DataFreshnessStatus,
  QualityScorecard,
  CircuitBreakerState,
  RateLimitStatus,
  SystemHealthSummary,
  MonitoringAlertLevel,
  DataQualityMetric,
} from './data-quality-monitoring'
import {
  DEFAULT_MONITORING_CONFIG,
  calculateStaleness,
  calculateQualityScore,
  evaluateAlertRule,
  getHealthStatusFromUptime,
} from './data-quality-monitoring'
import { DATA_CONNECTORS } from './data-connectors'
import { EXPANDED_SOURCES } from './expanded-catalog'

const MONITORING_STORAGE_KEY = 'chronos-monitoring-data'

interface MonitoringState {
  healthStatuses: APIHealthStatus[]
  alerts: MonitoringAlert[]
  callLogs: APICallLog[]
  freshnessStatuses: DataFreshnessStatus[]
  circuitBreakers: CircuitBreakerState[]
  rateLimits: RateLimitStatus[]
  lastUpdate: string
}

class MonitoringService {
  private state: MonitoringState
  private updateCallbacks: Set<() => void> = new Set()

  constructor() {
    this.state = this.loadState()
    this.initializeIfEmpty()
  }

  private loadState(): MonitoringState {
    try {
      const stored = localStorage.getItem(MONITORING_STORAGE_KEY)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (error) {
      console.warn('Failed to load monitoring state:', error)
    }

    return {
      healthStatuses: [],
      alerts: [],
      callLogs: [],
      freshnessStatuses: [],
      circuitBreakers: [],
      rateLimits: [],
      lastUpdate: new Date().toISOString(),
    }
  }

  private saveState(): void {
    try {
      localStorage.setItem(MONITORING_STORAGE_KEY, JSON.stringify(this.state))
    } catch (error) {
      console.warn('Failed to save monitoring state:', error)
    }
  }

  private initializeIfEmpty(): void {
    if (this.state.healthStatuses.length === 0) {
      this.state.healthStatuses = DATA_CONNECTORS.map((connector) =>
        this.generateInitialHealthStatus(connector.id, connector.sourceId, connector.name)
      )
      this.saveState()
    }
  }

  private generateInitialHealthStatus(
    connectorId: string,
    sourceId: string,
    name: string
  ): APIHealthStatus {
    const healthyChance = Math.random()
    const isHealthy = healthyChance > 0.15

    return {
      connectorId,
      sourceId,
      name,
      status: isHealthy ? 'healthy' : healthyChance > 0.05 ? 'degraded' : 'offline',
      lastSuccessfulFetch: isHealthy
        ? new Date(Date.now() - Math.random() * 3600000).toISOString()
        : undefined,
      lastFailedFetch: !isHealthy
        ? new Date(Date.now() - Math.random() * 600000).toISOString()
        : undefined,
      consecutiveFailures: isHealthy ? 0 : Math.floor(Math.random() * 5) + 1,
      uptime24h: isHealthy ? 0.98 + Math.random() * 0.02 : 0.7 + Math.random() * 0.2,
      uptime7d: isHealthy ? 0.97 + Math.random() * 0.03 : 0.75 + Math.random() * 0.15,
      responseTimeMs: isHealthy ? 500 + Math.random() * 1500 : 3000 + Math.random() * 5000,
      errorCount24h: isHealthy ? Math.floor(Math.random() * 3) : Math.floor(Math.random() * 25) + 5,
      requestCount24h: Math.floor(Math.random() * 500) + 100,
      currentRateLimit: {
        used: Math.floor(Math.random() * 80),
        limit: 100,
        resetAt: new Date(Date.now() + 60000).toISOString(),
      },
      circuitBreakerStatus: isHealthy ? 'closed' : healthyChance > 0.08 ? 'half-open' : 'open',
    }
  }

  subscribe(callback: () => void): () => void {
    this.updateCallbacks.add(callback)
    return () => {
      this.updateCallbacks.delete(callback)
    }
  }

  private notify(): void {
    this.updateCallbacks.forEach((callback) => callback())
  }

  getHealthStatuses(): APIHealthStatus[] {
    return this.state.healthStatuses
  }

  getHealthStatus(connectorId: string): APIHealthStatus | undefined {
    return this.state.healthStatuses.find((h) => h.connectorId === connectorId)
  }

  getAlerts(includeAcknowledged = false): MonitoringAlert[] {
    return this.state.alerts
      .filter((a) => includeAcknowledged || !a.acknowledgedAt)
      .sort((a, b) => {
        const levelOrder = { critical: 0, warning: 1, info: 2 }
        if (a.level !== b.level) {
          return levelOrder[a.level] - levelOrder[b.level]
        }
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      })
  }

  getCallLogs(limit = 100): APICallLog[] {
    return this.state.callLogs
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, limit)
  }

  getFreshnessStatuses(): DataFreshnessStatus[] {
    return this.state.freshnessStatuses
  }

  getCircuitBreakers(): CircuitBreakerState[] {
    return this.state.circuitBreakers
  }

  getRateLimits(): RateLimitStatus[] {
    return this.state.rateLimits
  }

  getSystemHealthSummary(): SystemHealthSummary {
    const statuses = this.state.healthStatuses
    const alerts = this.state.alerts.filter((a) => !a.acknowledgedAt && !a.resolvedAt)

    const healthyCount = statuses.filter((s) => s.status === 'healthy').length
    const degradedCount = statuses.filter((s) => s.status === 'degraded').length
    const offlineCount = statuses.filter((s) => s.status === 'offline').length

    const criticalAlerts = alerts.filter((a) => a.level === 'critical').length
    const warningAlerts = alerts.filter((a) => a.level === 'warning').length
    const infoAlerts = alerts.filter((a) => a.level === 'info').length

    const freshness = this.state.freshnessStatuses
    const currentCount = freshness.filter((f) => f.staleness === 'current').length
    const staleCount = freshness.filter((f) => f.staleness === 'stale').length
    const veryStaleCount = freshness.filter((f) => f.staleness === 'very-stale').length

    const totalRequests = statuses.reduce((sum, s) => sum + s.requestCount24h, 0)
    const totalErrors = statuses.reduce((sum, s) => sum + s.errorCount24h, 0)
    const avgResponseTime = statuses.length > 0
      ? statuses.reduce((sum, s) => sum + s.responseTimeMs, 0) / statuses.length
      : 0
    const successRate = totalRequests > 0 ? (totalRequests - totalErrors) / totalRequests : 1
    const errorRate = totalRequests > 0 ? totalErrors / totalRequests : 0

    let overallStatus: 'healthy' | 'degraded' | 'critical' = 'healthy'
    if (criticalAlerts > 0 || offlineCount > statuses.length * 0.3) {
      overallStatus = 'critical'
    } else if (warningAlerts > 0 || degradedCount > statuses.length * 0.2) {
      overallStatus = 'degraded'
    }

    return {
      timestamp: new Date().toISOString(),
      overallStatus,
      connectors: {
        total: statuses.length,
        healthy: healthyCount,
        degraded: degradedCount,
        offline: offlineCount,
      },
      alerts: {
        critical: criticalAlerts,
        warning: warningAlerts,
        info: infoAlerts,
      },
      dataFreshness: {
        current: currentCount,
        stale: staleCount,
        veryStale: veryStaleCount,
      },
      performance: {
        avgResponseTimeMs: Math.round(avgResponseTime),
        successRate: Math.round(successRate * 100) / 100,
        errorRate: Math.round(errorRate * 100) / 100,
      },
      nextScheduledRefresh: new Date(Date.now() + 3600000).toISOString(),
    }
  }

  simulateAPICall(connectorId: string): void {
    const connector = DATA_CONNECTORS.find((c) => c.id === connectorId)
    if (!connector) return

    const health = this.getHealthStatus(connectorId)
    if (!health) return

    const success = Math.random() > 0.1
    const responseTime = success ? 500 + Math.random() * 2000 : 3000 + Math.random() * 7000

    const log: APICallLog = {
      id: `log-${Date.now()}-${Math.random()}`,
      connectorId,
      sourceId: connector.sourceId,
      endpoint: `/api/data/${connector.sourceId}`,
      method: 'GET',
      timestamp: new Date().toISOString(),
      responseTimeMs: Math.round(responseTime),
      statusCode: success ? 200 : Math.random() > 0.5 ? 500 : 503,
      success,
      errorMessage: success ? undefined : 'Connection timeout',
      retryAttempt: 0,
    }

    this.state.callLogs.unshift(log)
    if (this.state.callLogs.length > 1000) {
      this.state.callLogs = this.state.callLogs.slice(0, 1000)
    }

    health.requestCount24h++
    if (!success) {
      health.errorCount24h++
      health.consecutiveFailures++
      health.lastFailedFetch = log.timestamp
    } else {
      health.consecutiveFailures = 0
      health.lastSuccessfulFetch = log.timestamp
    }

    health.responseTimeMs = Math.round((health.responseTimeMs * 0.8 + responseTime * 0.2))

    const errorRate = health.errorCount24h / health.requestCount24h
    if (health.consecutiveFailures >= 5) {
      health.status = 'offline'
      health.circuitBreakerStatus = 'open'
      this.createAlert('critical', 'api-availability', connectorId, connector.sourceId, health.name)
    } else if (errorRate > 0.3) {
      health.status = 'degraded'
      health.circuitBreakerStatus = 'half-open'
      this.createAlert('warning', 'error-rate', connectorId, connector.sourceId, health.name)
    } else {
      health.status = 'healthy'
      health.circuitBreakerStatus = 'closed'
    }

    this.state.lastUpdate = new Date().toISOString()
    this.saveState()
    this.notify()
  }

  private createAlert(
    level: MonitoringAlertLevel,
    type: string,
    connectorId: string,
    sourceId: string,
    name: string
  ): void {
    const existing = this.state.alerts.find(
      (a) => a.connectorId === connectorId && a.type === type && !a.resolvedAt
    )
    if (existing) return

    const alert: MonitoringAlert = {
      id: `alert-${Date.now()}-${Math.random()}`,
      level,
      type: type as any,
      sourceId,
      connectorId,
      title: level === 'critical' ? `${name} Offline` : `${name} Degraded Performance`,
      message:
        level === 'critical'
          ? `API connector has failed 5+ consecutive requests`
          : `Error rate exceeds 30%`,
      timestamp: new Date().toISOString(),
      relatedMetrics: [],
      actionItems: [
        'Check API endpoint status',
        'Review recent error logs',
        'Verify network connectivity',
        'Check rate limit status',
      ],
      affectedItems: [],
      estimatedImpact: level === 'critical' ? 'high' : 'medium',
    }

    this.state.alerts.unshift(alert)
    this.saveState()
    this.notify()
  }

  acknowledgeAlert(alertId: string, userId = 'current-user'): void {
    const alert = this.state.alerts.find((a) => a.id === alertId)
    if (alert && !alert.acknowledgedAt) {
      alert.acknowledgedAt = new Date().toISOString()
      alert.acknowledgedBy = userId
      this.saveState()
      this.notify()
    }
  }

  resolveAlert(alertId: string): void {
    const alert = this.state.alerts.find((a) => a.id === alertId)
    if (alert && !alert.resolvedAt) {
      alert.resolvedAt = new Date().toISOString()
      this.saveState()
      this.notify()
    }
  }

  refreshConnector(connectorId: string): void {
    this.simulateAPICall(connectorId)
  }

  simulateAPIFailure(connectorId: string): void {
    const connector = DATA_CONNECTORS.find((c) => c.id === connectorId)
    if (!connector) return

    const health = this.getHealthStatus(connectorId)
    if (!health) return

    for (let i = 0; i < 5; i++) {
      const responseTime = 5000 + Math.random() * 5000

      const log: APICallLog = {
        id: `log-${Date.now()}-${Math.random()}`,
        connectorId,
        sourceId: connector.sourceId,
        endpoint: `/api/data/${connector.sourceId}`,
        method: 'GET',
        timestamp: new Date(Date.now() - (4 - i) * 1000).toISOString(),
        responseTimeMs: Math.round(responseTime),
        statusCode: i % 2 === 0 ? 503 : 504,
        success: false,
        errorMessage: i % 2 === 0 ? 'Service unavailable' : 'Gateway timeout',
        retryAttempt: i,
      }

      this.state.callLogs.unshift(log)
    }

    if (this.state.callLogs.length > 1000) {
      this.state.callLogs = this.state.callLogs.slice(0, 1000)
    }

    health.consecutiveFailures = 5
    health.errorCount24h += 5
    health.requestCount24h += 5
    health.lastFailedFetch = new Date().toISOString()
    health.status = 'offline'
    health.circuitBreakerStatus = 'open'
    health.responseTimeMs = 7000

    this.createAlert('critical', 'api-availability', connectorId, connector.sourceId, health.name)

    this.state.lastUpdate = new Date().toISOString()
    this.saveState()
    this.notify()
  }

  getQualityScorecard(sourceId: string, period: '24h' | '7d' | '30d' = '24h'): QualityScorecard {
    const health = this.state.healthStatuses.find((h) => h.sourceId === sourceId)
    if (!health) {
      return {
        sourceId,
        period,
        scores: {
          availability: 0,
          freshness: 0,
          accuracy: 0,
          completeness: 0,
          consistency: 0,
          overall: 0,
        },
        trendDirection: 'stable',
        flagCount: { error: 0, warning: 0, info: 0 },
        recommendations: ['No data available'],
      }
    }

    const availability = period === '24h' ? health.uptime24h * 100 : health.uptime7d * 100
    const freshness = health.lastSuccessfulFetch ? 95 : 60
    const accuracy = 100 - (health.errorCount24h / health.requestCount24h) * 100
    const completeness = 90 + Math.random() * 10
    const consistency = 85 + Math.random() * 15
    const overall = calculateQualityScore({
      totalRequests: health.requestCount24h,
      successfulRequests: health.requestCount24h - health.errorCount24h,
      avgResponseTime: health.responseTimeMs,
      dataPointsCurrent: 100,
      dataPointsTotal: 120,
      errorFlags: health.errorCount24h > 10 ? 5 : health.errorCount24h > 5 ? 2 : 0,
      warningFlags: health.status === 'degraded' ? 3 : 0,
    })

    const recommendations: string[] = []
    if (availability < 95) recommendations.push('Investigate frequent connection failures')
    if (health.responseTimeMs > 3000) recommendations.push('Optimize API response time')
    if (health.errorCount24h > 10) recommendations.push('Review error patterns and implement retries')

    return {
      sourceId,
      period,
      scores: {
        availability: Math.round(availability),
        freshness: Math.round(freshness),
        accuracy: Math.round(accuracy),
        completeness: Math.round(completeness),
        consistency: Math.round(consistency),
        overall: Math.round(overall),
      },
      trendDirection: health.consecutiveFailures > 0 ? 'degrading' : 'stable',
      flagCount: {
        error: health.errorCount24h > 10 ? 5 : health.errorCount24h > 5 ? 2 : 0,
        warning: health.status === 'degraded' ? 3 : 0,
        info: 1,
      },
      recommendations,
    }
  }
}

export const monitoringService = new MonitoringService()
