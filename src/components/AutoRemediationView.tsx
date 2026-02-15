import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Play, 
  X, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Warning,
  ArrowClockwise,
  Trash,
  Gear,
  ChartLine
} from '@phosphor-icons/react'
import {
  autoRemediationService,
  type RemediationJob,
  type RemediationConfig,
  type RetryAttempt
} from '@/lib/auto-remediation'
import { cn } from '@/lib/utils'

export function AutoRemediationView() {
  const [jobs, setJobs] = useState<RemediationJob[]>([])
  const [config, setConfig] = useState<RemediationConfig>(autoRemediationService.getConfig())
  const [showConfig, setShowConfig] = useState(false)
  const [stats, setStats] = useState(autoRemediationService.getStats())

  useEffect(() => {
    const updateData = () => {
      setJobs(autoRemediationService.getJobs())
      setConfig(autoRemediationService.getConfig())
      setStats(autoRemediationService.getStats())
    }

    updateData()
    const unsubscribe = autoRemediationService.subscribe(updateData)
    
    const interval = setInterval(updateData, 2000)

    return () => {
      unsubscribe()
      clearInterval(interval)
    }
  }, [])

  const handleConfigUpdate = (updates: Partial<RemediationConfig>) => {
    autoRemediationService.updateConfig(updates)
  }

  const handleCancelJob = (jobId: string) => {
    autoRemediationService.cancelJob(jobId)
  }

  const handleRetryJob = (jobId: string) => {
    autoRemediationService.retryJob(jobId)
  }

  const handleClearCompleted = () => {
    autoRemediationService.clearCompletedJobs()
  }

  const activeJobs = jobs.filter(j => j.status === 'pending' || j.status === 'running')
  const completedJobs = jobs.filter(j => j.status === 'success' || j.status === 'failed' || j.status === 'cancelled')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold tracking-tight mb-2">
          Automated Remediation
        </h1>
        <p className="text-text-muted">
          Monitor and manage automated connector recovery workflows with exponential backoff
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-text-muted">Total Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-display">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-text-muted">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-display text-success">
              {(stats.successRate * 100).toFixed(0)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-text-muted">Avg Attempts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-display">
              {stats.avgAttemptsToSuccess.toFixed(1)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-text-muted">Avg Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-display">
              {(stats.avgDurationMs / 1000).toFixed(0)}s
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Gear size={20} />
                Configuration
              </CardTitle>
              <CardDescription>
                Control auto-remediation behavior and retry policies
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowConfig(!showConfig)}
            >
              {showConfig ? 'Hide' : 'Show'}
            </Button>
          </div>
        </CardHeader>
        
        {showConfig && (
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="enabled">Auto-Remediation Enabled</Label>
                <Switch
                  id="enabled"
                  checked={config.enabled}
                  onCheckedChange={(checked) => handleConfigUpdate({ enabled: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="notifications">Notifications Enabled</Label>
                <Switch
                  id="notifications"
                  checked={config.notificationsEnabled}
                  onCheckedChange={(checked) => handleConfigUpdate({ notificationsEnabled: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="circuit-breaker">Auto-Retry Circuit Breaker</Label>
                <Switch
                  id="circuit-breaker"
                  checked={config.circuitBreakerAutoRetryEnabled}
                  onCheckedChange={(checked) => handleConfigUpdate({ circuitBreakerAutoRetryEnabled: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="jitter">Jitter Enabled</Label>
                <Switch
                  id="jitter"
                  checked={config.jitterEnabled}
                  onCheckedChange={(checked) => handleConfigUpdate({ jitterEnabled: checked })}
                />
              </div>
            </div>

            <Separator />

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-xs text-text-muted">Max Retries: {config.maxRetries}</Label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={config.maxRetries}
                  onChange={(e) => handleConfigUpdate({ maxRetries: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs text-text-muted">Backoff Multiplier: {config.backoffMultiplier}x</Label>
                <input
                  type="range"
                  min="1.5"
                  max="3"
                  step="0.1"
                  value={config.backoffMultiplier}
                  onChange={(e) => handleConfigUpdate({ backoffMultiplier: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs text-text-muted">Initial Backoff: {config.initialBackoffMs}ms</Label>
                <input
                  type="range"
                  min="500"
                  max="5000"
                  step="500"
                  value={config.initialBackoffMs}
                  onChange={(e) => handleConfigUpdate({ initialBackoffMs: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs text-text-muted">Max Backoff: {config.maxBackoffMs / 1000}s</Label>
                <input
                  type="range"
                  min="10000"
                  max="300000"
                  step="10000"
                  value={config.maxBackoffMs}
                  onChange={(e) => handleConfigUpdate({ maxBackoffMs: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <ChartLine size={20} />
                Active Remediation Jobs
              </CardTitle>
              <CardDescription>
                Currently running or pending retry attempts
              </CardDescription>
            </div>
            <Badge variant={activeJobs.length > 0 ? 'default' : 'secondary'}>
              {activeJobs.length} active
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {activeJobs.length === 0 ? (
            <div className="text-center py-8 text-text-muted">
              <CheckCircle size={48} className="mx-auto mb-2 opacity-50" />
              <p>No active remediation jobs</p>
            </div>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {activeJobs.map(job => (
                  <RemediationJobCard
                    key={job.id}
                    job={job}
                    onCancel={handleCancelJob}
                    onRetry={handleRetryJob}
                  />
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Completed Jobs</CardTitle>
              <CardDescription>
                Recently finished remediation attempts
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline" className="border-success text-success">
                {stats.success} success
              </Badge>
              <Badge variant="outline" className="border-danger text-danger">
                {stats.failed} failed
              </Badge>
              {completedJobs.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearCompleted}
                >
                  <Trash size={16} className="mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {completedJobs.length === 0 ? (
            <div className="text-center py-8 text-text-muted">
              <Clock size={48} className="mx-auto mb-2 opacity-50" />
              <p>No completed jobs</p>
            </div>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {completedJobs.map(job => (
                  <RemediationJobCard
                    key={job.id}
                    job={job}
                    onCancel={handleCancelJob}
                    onRetry={handleRetryJob}
                  />
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function RemediationJobCard({
  job,
  onCancel,
  onRetry,
}: {
  job: RemediationJob
  onCancel: (id: string) => void
  onRetry: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)

  const getStatusBadge = () => {
    switch (job.status) {
      case 'pending':
        return <Badge variant="outline" className="border-warning text-warning">Pending</Badge>
      case 'running':
        return <Badge variant="outline" className="border-info text-info">Running</Badge>
      case 'success':
        return <Badge variant="outline" className="border-success text-success">Success</Badge>
      case 'failed':
        return <Badge variant="outline" className="border-danger text-danger">Failed</Badge>
      case 'cancelled':
        return <Badge variant="outline">Cancelled</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const getStatusIcon = () => {
    switch (job.status) {
      case 'pending':
        return <Clock size={16} className="text-warning" />
      case 'running':
        return <ArrowClockwise size={16} className="text-info animate-spin" />
      case 'success':
        return <CheckCircle size={16} className="text-success" />
      case 'failed':
        return <XCircle size={16} className="text-danger" />
      case 'cancelled':
        return <X size={16} className="text-text-muted" />
      default:
        return <Warning size={16} />
    }
  }

  const getReasonLabel = (reason: RemediationJob['reason']) => {
    switch (reason) {
      case 'circuit-breaker-open':
        return 'Circuit Breaker Open'
      case 'high-error-rate':
        return 'High Error Rate'
      case 'consecutive-failures':
        return 'Consecutive Failures'
      case 'manual-trigger':
        return 'Manual Trigger'
      default:
        return 'Unknown'
    }
  }

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    return `${minutes}m ${seconds % 60}s`
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return (
    <div className="border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-mono font-semibold">{job.sourceId}</span>
            {getStatusBadge()}
          </div>
          <p className="text-sm text-text-muted">
            Reason: {getReasonLabel(job.reason)}
          </p>
          <p className="text-xs text-text-muted">
            Created: {formatTimestamp(job.createdAt)}
          </p>
        </div>
        <div className="flex gap-2">
          {(job.status === 'pending' || job.status === 'running') && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onCancel(job.id)}
            >
              <X size={16} />
            </Button>
          )}
          {(job.status === 'failed' || job.status === 'cancelled') && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRetry(job.id)}
            >
              <ArrowClockwise size={16} />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Hide' : 'Details'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <div className="text-text-muted text-xs">Attempts</div>
          <div className="font-mono font-semibold">{job.attempts.length}</div>
        </div>
        <div>
          <div className="text-text-muted text-xs">Next Retry</div>
          <div className="font-mono text-xs">
            {job.nextRetryAt ? formatTimestamp(job.nextRetryAt) : 'N/A'}
          </div>
        </div>
        <div>
          <div className="text-text-muted text-xs">Duration</div>
          <div className="font-mono font-semibold">
            {job.totalDurationMs ? formatDuration(job.totalDurationMs) : 'In progress'}
          </div>
        </div>
      </div>

      {expanded && (
        <>
          <Separator />
          <div className="space-y-2">
            <div className="text-sm font-semibold">Retry Attempts</div>
            <div className="space-y-2">
              {job.attempts.map((attempt, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "flex items-center justify-between text-xs p-2 rounded border",
                    attempt.success 
                      ? "border-success bg-success/5" 
                      : "border-danger bg-danger/5"
                  )}
                >
                  <div className="flex items-center gap-2">
                    {attempt.success ? (
                      <CheckCircle size={14} className="text-success" />
                    ) : (
                      <XCircle size={14} className="text-danger" />
                    )}
                    <span className="font-mono">Attempt #{attempt.attemptNumber}</span>
                  </div>
                  <div className="flex items-center gap-3 text-text-muted">
                    {attempt.delayMs > 0 && (
                      <span>Delay: {(attempt.delayMs / 1000).toFixed(1)}s</span>
                    )}
                    {attempt.responseTimeMs && (
                      <span>Response: {attempt.responseTimeMs}ms</span>
                    )}
                    <span>{formatTimestamp(attempt.timestamp)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {job.errorMessage && (
            <>
              <Separator />
              <div className="text-xs space-y-1">
                <div className="font-semibold text-danger">Error Message</div>
                <div className="text-text-muted font-mono">{job.errorMessage}</div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
