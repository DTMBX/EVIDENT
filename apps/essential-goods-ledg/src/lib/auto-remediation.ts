import type { DataConnector } from './types'
import { monitoringService } from './monitoring-service'
import { toast } from 'sonner'

export interface RetryAttempt {
  attemptNumber: number
  timestamp: string
  delayMs: number
  success: boolean
  errorMessage?: string
  responseTimeMs?: number
}

export interface RemediationJob {
  id: string
  connectorId: string
  sourceId: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  createdAt: string
  startedAt?: string
  completedAt?: string
  attempts: RetryAttempt[]
  currentBackoffMs: number
  nextRetryAt?: string
  reason: 'circuit-breaker-open' | 'high-error-rate' | 'consecutive-failures' | 'manual-trigger'
  errorMessage?: string
  totalDurationMs?: number
}

export interface RemediationConfig {
  enabled: boolean
  maxRetries: number
  initialBackoffMs: number
  maxBackoffMs: number
  backoffMultiplier: number
  jitterEnabled: boolean
  jitterMaxMs: number
  autoTriggerThreshold: number
  circuitBreakerAutoRetryEnabled: boolean
  circuitBreakerRetryIntervalMs: number
  notificationsEnabled: boolean
}

export const DEFAULT_REMEDIATION_CONFIG: RemediationConfig = {
  enabled: true,
  maxRetries: 5,
  initialBackoffMs: 1000,
  maxBackoffMs: 60000,
  backoffMultiplier: 2,
  jitterEnabled: true,
  jitterMaxMs: 500,
  autoTriggerThreshold: 3,
  circuitBreakerAutoRetryEnabled: true,
  circuitBreakerRetryIntervalMs: 300000,
  notificationsEnabled: true,
}

class AutoRemediationService {
  private jobs: Map<string, RemediationJob> = new Map()
  private config: RemediationConfig = DEFAULT_REMEDIATION_CONFIG
  private activeTimers: Map<string, NodeJS.Timeout> = new Map()
  private updateCallbacks: Set<() => void> = new Set()
  private circuitBreakerMonitors: Map<string, NodeJS.Timeout> = new Map()

  constructor() {
    this.loadConfig()
    this.loadJobs()
    this.startCircuitBreakerMonitoring()
  }

  private loadConfig(): void {
    try {
      const stored = localStorage.getItem('chronos-remediation-config')
      if (stored) {
        this.config = { ...DEFAULT_REMEDIATION_CONFIG, ...JSON.parse(stored) }
      }
    } catch (error) {
      console.warn('Failed to load remediation config:', error)
    }
  }

  private saveConfig(): void {
    try {
      localStorage.setItem('chronos-remediation-config', JSON.stringify(this.config))
    } catch (error) {
      console.warn('Failed to save remediation config:', error)
    }
  }

  private loadJobs(): void {
    try {
      const stored = localStorage.getItem('chronos-remediation-jobs')
      if (stored) {
        const jobs: RemediationJob[] = JSON.parse(stored)
        jobs.forEach(job => {
          this.jobs.set(job.id, job)
          if (job.status === 'pending' && job.nextRetryAt) {
            this.scheduleRetry(job)
          }
        })
      }
    } catch (error) {
      console.warn('Failed to load remediation jobs:', error)
    }
  }

  private saveJobs(): void {
    try {
      const jobs = Array.from(this.jobs.values())
      localStorage.setItem('chronos-remediation-jobs', JSON.stringify(jobs))
    } catch (error) {
      console.warn('Failed to save remediation jobs:', error)
    }
  }

  private notify(): void {
    this.updateCallbacks.forEach(callback => callback())
  }

  subscribe(callback: () => void): () => void {
    this.updateCallbacks.add(callback)
    return () => {
      this.updateCallbacks.delete(callback)
    }
  }

  getConfig(): RemediationConfig {
    return { ...this.config }
  }

  updateConfig(updates: Partial<RemediationConfig>): void {
    this.config = { ...this.config, ...updates }
    this.saveConfig()
    this.notify()
  }

  getJobs(): RemediationJob[] {
    return Array.from(this.jobs.values())
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  }

  getJob(jobId: string): RemediationJob | undefined {
    return this.jobs.get(jobId)
  }

  getActiveJobsForConnector(connectorId: string): RemediationJob[] {
    return Array.from(this.jobs.values())
      .filter(job => 
        job.connectorId === connectorId && 
        (job.status === 'pending' || job.status === 'running')
      )
  }

  private calculateBackoff(attemptNumber: number, baseBackoffMs: number): number {
    const exponentialBackoff = baseBackoffMs * Math.pow(this.config.backoffMultiplier, attemptNumber - 1)
    const cappedBackoff = Math.min(exponentialBackoff, this.config.maxBackoffMs)
    
    if (this.config.jitterEnabled) {
      const jitter = Math.random() * this.config.jitterMaxMs
      return cappedBackoff + jitter
    }
    
    return cappedBackoff
  }

  private startCircuitBreakerMonitoring(): void {
    const checkInterval = setInterval(() => {
      if (!this.config.enabled || !this.config.circuitBreakerAutoRetryEnabled) {
        return
      }

      const healthStatuses = monitoringService.getHealthStatuses()
      
      healthStatuses.forEach(health => {
        if (health.circuitBreakerStatus === 'open') {
          const existingJobs = this.getActiveJobsForConnector(health.connectorId)
          
          if (existingJobs.length === 0) {
            this.createRemediationJob(
              health.connectorId,
              health.sourceId,
              'circuit-breaker-open'
            )
          }
        }
      })
    }, this.config.circuitBreakerRetryIntervalMs)

    this.circuitBreakerMonitors.set('global', checkInterval as any)
  }

  createRemediationJob(
    connectorId: string,
    sourceId: string,
    reason: RemediationJob['reason']
  ): RemediationJob {
    const job: RemediationJob = {
      id: `remediation-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      connectorId,
      sourceId,
      status: 'pending',
      createdAt: new Date().toISOString(),
      attempts: [],
      currentBackoffMs: this.config.initialBackoffMs,
      reason,
    }

    this.jobs.set(job.id, job)
    this.saveJobs()
    
    if (this.config.enabled) {
      this.executeJob(job.id)
    }

    if (this.config.notificationsEnabled) {
      toast.info(`Auto-remediation started for ${sourceId}`, {
        description: `Attempting to restore connector (${this.getReasonLabel(reason)})`,
      })
    }

    this.notify()
    return job
  }

  async executeJob(jobId: string): Promise<void> {
    const job = this.jobs.get(jobId)
    if (!job || job.status === 'cancelled') {
      return
    }

    job.status = 'running'
    if (!job.startedAt) {
      job.startedAt = new Date().toISOString()
    }
    
    const attemptNumber = job.attempts.length + 1
    const backoffMs = this.calculateBackoff(attemptNumber, this.config.initialBackoffMs)
    
    this.saveJobs()
    this.notify()

    const attempt: RetryAttempt = {
      attemptNumber,
      timestamp: new Date().toISOString(),
      delayMs: attemptNumber > 1 ? backoffMs : 0,
      success: false,
    }

    try {
      const startTime = Date.now()
      
      await new Promise(resolve => setTimeout(resolve, attempt.delayMs))
      
      monitoringService.simulateAPICall(job.connectorId)
      
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const health = monitoringService.getHealthStatus(job.connectorId)
      const responseTime = Date.now() - startTime
      
      if (health && health.status === 'healthy' && health.circuitBreakerStatus === 'closed') {
        attempt.success = true
        attempt.responseTimeMs = responseTime
        job.attempts.push(attempt)
        job.status = 'success'
        job.completedAt = new Date().toISOString()
        job.totalDurationMs = new Date(job.completedAt).getTime() - new Date(job.createdAt).getTime()

        if (this.config.notificationsEnabled) {
          toast.success(`Connector restored: ${job.sourceId}`, {
            description: `Successfully recovered after ${job.attempts.length} attempt(s)`,
          })
        }
      } else {
        throw new Error(health?.circuitBreakerStatus === 'open' ? 'Circuit breaker still open' : 'Connector still degraded')
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      attempt.errorMessage = errorMessage
      job.attempts.push(attempt)

      if (attemptNumber >= this.config.maxRetries) {
        job.status = 'failed'
        job.completedAt = new Date().toISOString()
        job.totalDurationMs = new Date(job.completedAt).getTime() - new Date(job.createdAt).getTime()
        job.errorMessage = `Failed after ${this.config.maxRetries} attempts: ${errorMessage}`

        if (this.config.notificationsEnabled) {
          toast.error(`Remediation failed: ${job.sourceId}`, {
            description: `Unable to restore connector after ${this.config.maxRetries} attempts`,
          })
        }
      } else {
        job.status = 'pending'
        job.currentBackoffMs = backoffMs
        job.nextRetryAt = new Date(Date.now() + backoffMs).toISOString()
        
        this.scheduleRetry(job)
      }
    }

    this.saveJobs()
    this.notify()
  }

  private scheduleRetry(job: RemediationJob): void {
    if (!job.nextRetryAt) {
      return
    }

    const existingTimer = this.activeTimers.get(job.id)
    if (existingTimer) {
      clearTimeout(existingTimer)
    }

    const delay = new Date(job.nextRetryAt).getTime() - Date.now()
    
    const timer = setTimeout(() => {
      this.executeJob(job.id)
      this.activeTimers.delete(job.id)
    }, Math.max(0, delay))

    this.activeTimers.set(job.id, timer as any)
  }

  cancelJob(jobId: string): void {
    const job = this.jobs.get(jobId)
    if (!job) {
      return
    }

    if (job.status === 'pending' || job.status === 'running') {
      job.status = 'cancelled'
      job.completedAt = new Date().toISOString()
      
      const timer = this.activeTimers.get(jobId)
      if (timer) {
        clearTimeout(timer)
        this.activeTimers.delete(jobId)
      }

      this.saveJobs()
      this.notify()

      if (this.config.notificationsEnabled) {
        toast.info(`Remediation cancelled: ${job.sourceId}`)
      }
    }
  }

  retryJob(jobId: string): void {
    const job = this.jobs.get(jobId)
    if (!job) {
      return
    }

    if (job.status === 'failed' || job.status === 'cancelled') {
      job.status = 'pending'
      job.attempts = []
      job.currentBackoffMs = this.config.initialBackoffMs
      job.nextRetryAt = undefined
      job.errorMessage = undefined
      job.completedAt = undefined
      job.totalDurationMs = undefined

      this.saveJobs()
      this.executeJob(job.id)
      this.notify()
    }
  }

  clearCompletedJobs(): void {
    const completed = Array.from(this.jobs.values())
      .filter(job => job.status === 'success' || job.status === 'failed' || job.status === 'cancelled')
      .map(job => job.id)

    completed.forEach(id => this.jobs.delete(id))
    this.saveJobs()
    this.notify()
  }

  private getReasonLabel(reason: RemediationJob['reason']): string {
    switch (reason) {
      case 'circuit-breaker-open':
        return 'Circuit breaker open'
      case 'high-error-rate':
        return 'High error rate'
      case 'consecutive-failures':
        return 'Consecutive failures'
      case 'manual-trigger':
        return 'Manual trigger'
      default:
        return 'Unknown'
    }
  }

  getStats(): {
    total: number
    pending: number
    running: number
    success: number
    failed: number
    cancelled: number
    successRate: number
    avgAttemptsToSuccess: number
    avgDurationMs: number
  } {
    const jobs = Array.from(this.jobs.values())
    
    const total = jobs.length
    const pending = jobs.filter(j => j.status === 'pending').length
    const running = jobs.filter(j => j.status === 'running').length
    const success = jobs.filter(j => j.status === 'success').length
    const failed = jobs.filter(j => j.status === 'failed').length
    const cancelled = jobs.filter(j => j.status === 'cancelled').length
    
    const completed = success + failed
    const successRate = completed > 0 ? success / completed : 0
    
    const successfulJobs = jobs.filter(j => j.status === 'success')
    const avgAttemptsToSuccess = successfulJobs.length > 0
      ? successfulJobs.reduce((sum, j) => sum + j.attempts.length, 0) / successfulJobs.length
      : 0
    
    const completedWithDuration = jobs.filter(j => j.totalDurationMs !== undefined)
    const avgDurationMs = completedWithDuration.length > 0
      ? completedWithDuration.reduce((sum, j) => sum + (j.totalDurationMs || 0), 0) / completedWithDuration.length
      : 0

    return {
      total,
      pending,
      running,
      success,
      failed,
      cancelled,
      successRate,
      avgAttemptsToSuccess,
      avgDurationMs,
    }
  }

  destroy(): void {
    this.activeTimers.forEach(timer => clearTimeout(timer))
    this.activeTimers.clear()
    
    this.circuitBreakerMonitors.forEach(monitor => clearInterval(monitor))
    this.circuitBreakerMonitors.clear()
    
    this.updateCallbacks.clear()
  }
}

export const autoRemediationService = new AutoRemediationService()
