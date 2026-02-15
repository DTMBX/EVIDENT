import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import {
  Pulse,
  Warning,
  CheckCircle,
  XCircle,
  Clock,
  Lightning,
  TrendUp,
  TrendDown,
  Minus,
  ArrowsClockwise,
  Database,
  Bell,
  Gear,
  Archive,
  Info,
} from '@phosphor-icons/react'
import { monitoringService } from '@/lib/monitoring-service'
import type {
  APIHealthStatus,
  MonitoringAlert,
  SystemHealthSummary,
  QualityScorecard,
} from '@/lib/data-quality-monitoring'
import { cn } from '@/lib/utils'

export function DataQualityMonitoringView() {
  const [summary, setSummary] = useState<SystemHealthSummary | null>(null)
  const [healthStatuses, setHealthStatuses] = useState<APIHealthStatus[]>([])
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([])
  const [selectedConnector, setSelectedConnector] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState<Set<string>>(new Set())
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true)

  const loadData = () => {
    setSummary(monitoringService.getSystemHealthSummary())
    setHealthStatuses(monitoringService.getHealthStatuses())
    setAlerts(monitoringService.getAlerts())
  }

  useEffect(() => {
    loadData()
    const unsubscribe = monitoringService.subscribe(() => {
      loadData()
    })

    return unsubscribe
  }, [])

  useEffect(() => {
    if (!autoRefreshEnabled) return

    const interval = setInterval(() => {
      loadData()
    }, 30000)

    return () => clearInterval(interval)
  }, [autoRefreshEnabled])

  const handleRefreshConnector = async (connectorId: string) => {
    setRefreshing((prev) => new Set(prev).add(connectorId))
    
    await new Promise((resolve) => setTimeout(resolve, 1000))
    monitoringService.refreshConnector(connectorId)
    
    setRefreshing((prev) => {
      const next = new Set(prev)
      next.delete(connectorId)
      return next
    })
  }

  const handleAcknowledgeAlert = (alertId: string) => {
    monitoringService.acknowledgeAlert(alertId)
  }

  const handleResolveAlert = (alertId: string) => {
    monitoringService.resolveAlert(alertId)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="text-success" weight="fill" />
      case 'degraded':
        return <Warning className="text-warning" weight="fill" />
      case 'offline':
        return <XCircle className="text-danger" weight="fill" />
      default:
        return <Clock className="text-muted-foreground" />
    }
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'text-success bg-success/10 border-success/20'
      case 'degraded':
        return 'text-warning bg-warning/10 border-warning/20'
      case 'offline':
        return 'text-danger bg-danger/10 border-danger/20'
      default:
        return 'text-muted-foreground bg-muted border-border'
    }
  }

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <XCircle className="text-danger" weight="fill" />
      case 'warning':
        return <Warning className="text-warning" weight="fill" />
      case 'info':
        return <Info className="text-info" weight="fill" />
      default:
        return <Bell />
    }
  }

  const activeAlerts = alerts.filter((a) => !a.acknowledgedAt && !a.resolvedAt)
  const criticalAlerts = activeAlerts.filter((a) => a.level === 'critical')

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight">
            Data Quality Monitoring
          </h1>
          <p className="text-text-muted mt-1">
            Real-time API health, data freshness, and alert management
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.hash = 'remediation'}
          >
            <Gear className="mr-2" />
            Auto-Remediation
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
          >
            <Pulse className={cn('mr-2', autoRefreshEnabled && 'animate-pulse')} />
            {autoRefreshEnabled ? 'Auto-refresh On' : 'Auto-refresh Off'}
          </Button>
          <Button variant="outline" size="sm" onClick={loadData}>
            <ArrowsClockwise className="mr-2" />
            Refresh Now
          </Button>
        </div>
      </div>

      {summary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">System Status</p>
                <p className="text-2xl font-bold font-display mt-2">
                  {summary.overallStatus === 'healthy' ? 'Healthy' : 
                   summary.overallStatus === 'degraded' ? 'Degraded' : 'Critical'}
                </p>
              </div>
              <div className={cn('rounded-full p-3', getStatusColor(summary.overallStatus))}>
                {getStatusIcon(summary.overallStatus)}
              </div>
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs text-text-muted">
              <span className="flex items-center gap-1">
                <CheckCircle className="text-success" size={14} />
                {summary.connectors.healthy}
              </span>
              <span className="flex items-center gap-1">
                <Warning className="text-warning" size={14} />
                {summary.connectors.degraded}
              </span>
              <span className="flex items-center gap-1">
                <XCircle className="text-danger" size={14} />
                {summary.connectors.offline}
              </span>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">Active Alerts</p>
                <p className="text-2xl font-bold font-display mt-2">
                  {activeAlerts.length}
                </p>
              </div>
              <div className={cn('rounded-full p-3', 
                criticalAlerts.length > 0 ? 'text-danger bg-danger/10' : 'text-muted-foreground bg-muted'
              )}>
                <Bell weight={criticalAlerts.length > 0 ? 'fill' : 'regular'} />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs text-text-muted">
              <span>Critical: {summary.alerts.critical}</span>
              <span>Warning: {summary.alerts.warning}</span>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">Success Rate</p>
                <p className="text-2xl font-bold font-display mt-2">
                  {(summary.performance.successRate * 100).toFixed(1)}%
                </p>
              </div>
              <div className={cn('rounded-full p-3',
                summary.performance.successRate >= 0.95 ? 'text-success bg-success/10' : 'text-warning bg-warning/10'
              )}>
                <TrendUp />
              </div>
            </div>
            <div className="mt-4">
              <Progress 
                value={summary.performance.successRate * 100} 
                className="h-2"
              />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">Avg Response</p>
                <p className="text-2xl font-bold font-display mt-2">
                  {summary.performance.avgResponseTimeMs}ms
                </p>
              </div>
              <div className={cn('rounded-full p-3',
                summary.performance.avgResponseTimeMs < 3000 ? 'text-success bg-success/10' : 'text-warning bg-warning/10'
              )}>
                <Lightning />
              </div>
            </div>
            <div className="mt-4 text-xs text-text-muted">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </Card>
        </div>
      )}

      {criticalAlerts.length > 0 && (
        <Alert variant="destructive" className="border-danger bg-danger/5">
          <Warning className="h-5 w-5" />
          <AlertTitle className="font-display font-semibold">Critical Alerts Active</AlertTitle>
          <AlertDescription>
            {criticalAlerts.length} critical {criticalAlerts.length === 1 ? 'alert requires' : 'alerts require'} immediate attention.
            API connectors may be offline or experiencing severe issues.
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="connectors" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-auto lg:inline-grid">
          <TabsTrigger value="connectors" className="gap-2">
            <Database size={16} />
            Connectors
          </TabsTrigger>
          <TabsTrigger value="alerts" className="gap-2">
            <Bell size={16} />
            Alerts
            {activeAlerts.length > 0 && (
              <Badge variant="destructive" className="ml-1 h-5 min-w-5 px-1 text-xs">
                {activeAlerts.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <Archive size={16} />
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="connectors" className="space-y-4">
          {healthStatuses.map((health) => (
            <ConnectorHealthCard
              key={health.connectorId}
              health={health}
              isRefreshing={refreshing.has(health.connectorId)}
              onRefresh={() => handleRefreshConnector(health.connectorId)}
              onSelect={() => setSelectedConnector(health.connectorId)}
            />
          ))}
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          {activeAlerts.length === 0 ? (
            <Card className="p-12 text-center">
              <CheckCircle size={48} className="mx-auto text-success mb-4" weight="fill" />
              <p className="text-lg font-display font-semibold">No Active Alerts</p>
              <p className="text-text-muted mt-2">All systems are operating normally</p>
            </Card>
          ) : (
            activeAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onAcknowledge={() => handleAcknowledgeAlert(alert.id)}
                onResolve={() => handleResolveAlert(alert.id)}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card className="p-6">
            <h3 className="font-display font-semibold text-lg mb-4">Recent API Calls</h3>
            <ScrollArea className="h-[500px]">
              <CallLogsList />
            </ScrollArea>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ConnectorHealthCard({
  health,
  isRefreshing,
  onRefresh,
  onSelect,
}: {
  health: APIHealthStatus
  isRefreshing: boolean
  onRefresh: () => void
  onSelect: () => void
}) {
  const [scorecard, setScorecard] = useState<QualityScorecard | null>(null)

  useEffect(() => {
    setScorecard(monitoringService.getQualityScorecard(health.sourceId))
  }, [health.sourceId])

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={onSelect}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4 flex-1">
          <div className={cn('rounded-lg p-3 mt-1', 
            health.status === 'healthy' ? 'bg-success/10 text-success' :
            health.status === 'degraded' ? 'bg-warning/10 text-warning' :
            'bg-danger/10 text-danger'
          )}>
            {getStatusIcon(health.status)}
          </div>

          <div className="flex-1 space-y-3">
            <div>
              <div className="flex items-center gap-3">
                <h3 className="font-display font-semibold text-lg">{health.name}</h3>
                <Badge variant={
                  health.status === 'healthy' ? 'default' :
                  health.status === 'degraded' ? 'secondary' : 'destructive'
                } className="capitalize">
                  {health.status}
                </Badge>
                {health.circuitBreakerStatus !== 'closed' && (
                  <Badge variant="outline" className="text-xs">
                    Circuit: {health.circuitBreakerStatus}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-text-muted mt-1">
                Source: {health.sourceId}
              </p>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-text-muted">24h Uptime</p>
                <p className="font-display font-semibold text-lg mt-1">
                  {(health.uptime24h * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Response Time</p>
                <p className="font-display font-semibold text-lg mt-1">
                  {health.responseTimeMs}ms
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Errors (24h)</p>
                <p className="font-display font-semibold text-lg mt-1">
                  {health.errorCount24h}
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Rate Limit</p>
                <p className="font-display font-semibold text-lg mt-1">
                  {health.currentRateLimit.used}/{health.currentRateLimit.limit}
                </p>
              </div>
            </div>

            {scorecard && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-text-muted">Quality Score</p>
                  <p className="text-sm font-display font-semibold">{scorecard.scores.overall}/100</p>
                </div>
                <Progress value={scorecard.scores.overall} className="h-2" />
              </div>
            )}

            {health.lastSuccessfulFetch && (
              <p className="text-xs text-text-muted">
                Last successful fetch: {new Date(health.lastSuccessfulFetch).toLocaleString()}
              </p>
            )}
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onRefresh()
          }}
          disabled={isRefreshing}
        >
          <ArrowsClockwise className={cn('mr-2', isRefreshing && 'animate-spin')} />
          {isRefreshing ? 'Refreshing...' : 'Test'}
        </Button>
      </div>
    </Card>
  )
}

function AlertCard({
  alert,
  onAcknowledge,
  onResolve,
}: {
  alert: MonitoringAlert
  onAcknowledge: () => void
  onResolve: () => void
}) {
  return (
    <Card className={cn('p-6 border-l-4',
      alert.level === 'critical' ? 'border-l-danger' :
      alert.level === 'warning' ? 'border-l-warning' : 'border-l-info'
    )}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4 flex-1">
          <div className="mt-1">
            {getAlertIcon(alert.level)}
          </div>

          <div className="flex-1 space-y-3">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h3 className="font-display font-semibold text-lg">{alert.title}</h3>
                <Badge variant={
                  alert.level === 'critical' ? 'destructive' :
                  alert.level === 'warning' ? 'secondary' : 'default'
                } className="capitalize">
                  {alert.level}
                </Badge>
              </div>
              <p className="text-sm text-text-secondary">{alert.message}</p>
              <p className="text-xs text-text-muted mt-2">
                {new Date(alert.timestamp).toLocaleString()}
              </p>
            </div>

            {alert.actionItems.length > 0 && (
              <div>
                <p className="text-sm font-semibold mb-2">Recommended Actions:</p>
                <ul className="text-sm text-text-muted space-y-1">
                  {alert.actionItems.map((action, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Minus size={16} className="mt-0.5 shrink-0" />
                      {action}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          {!alert.acknowledgedAt && (
            <Button variant="outline" size="sm" onClick={onAcknowledge}>
              Acknowledge
            </Button>
          )}
          <Button variant="default" size="sm" onClick={onResolve}>
            Resolve
          </Button>
        </div>
      </div>
    </Card>
  )
}

function CallLogsList() {
  const [logs, setLogs] = useState(monitoringService.getCallLogs(50))

  return (
    <div className="space-y-2">
      {logs.map((log) => (
        <div
          key={log.id}
          className={cn(
            'flex items-center justify-between gap-4 p-3 rounded-lg border',
            log.success ? 'border-border' : 'border-danger/20 bg-danger/5'
          )}
        >
          <div className="flex items-center gap-3 flex-1">
            {log.success ? (
              <CheckCircle size={20} className="text-success shrink-0" />
            ) : (
              <XCircle size={20} className="text-danger shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-display font-semibold truncate">{log.endpoint}</p>
              <p className="text-xs text-text-muted">
                {new Date(log.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className={cn('font-mono', log.success ? 'text-success' : 'text-danger')}>
              {log.statusCode}
            </span>
            <span className="text-text-muted">{log.responseTimeMs}ms</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'healthy':
      return <CheckCircle size={24} weight="fill" />
    case 'degraded':
      return <Warning size={24} weight="fill" />
    case 'offline':
      return <XCircle size={24} weight="fill" />
    default:
      return <Clock size={24} />
  }
}

function getAlertIcon(level: string) {
  switch (level) {
    case 'critical':
      return <XCircle size={24} weight="fill" />
    case 'warning':
      return <Warning size={24} weight="fill" />
    case 'info':
      return <Info size={24} weight="fill" />
    default:
      return <Bell size={24} />
  }
}
