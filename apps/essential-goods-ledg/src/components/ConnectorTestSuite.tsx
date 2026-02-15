import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Play, 
  Stop,
  CheckCircle, 
  XCircle, 
  Clock, 
  Warning,
  Pulse,
  Flask,
  Bug,
  Wrench,
  ChartLineUp,
  ArrowClockwise
} from '@phosphor-icons/react'
import { monitoringService } from '@/lib/monitoring-service'
import { autoRemediationService, type RemediationJob } from '@/lib/auto-remediation'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'

interface TestScenario {
  id: string
  name: string
  description: string
  duration: number
  failureType: 'timeout' | 'rate-limit' | 'network' | 'auth' | 'data-corruption' | 'intermittent'
  connectorId: string
  expectedOutcome: string
  status: 'idle' | 'running' | 'passed' | 'failed'
  steps: TestStep[]
}

interface TestStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime?: number
  endTime?: number
  details?: string
}

const TEST_SCENARIOS: Omit<TestScenario, 'status' | 'steps'>[] = [
  {
    id: 'scenario-1',
    name: 'Circuit Breaker Opens After Consecutive Failures',
    description: 'Simulate 5 consecutive API failures to trigger circuit breaker, then watch auto-remediation restore service',
    duration: 45,
    failureType: 'network',
    connectorId: 'usda-api',
    expectedOutcome: 'Circuit breaker opens → Auto-remediation triggered → Connector restored with exponential backoff'
  },
  {
    id: 'scenario-2',
    name: 'Rate Limit Exhaustion Recovery',
    description: 'Exhaust API rate limits and verify graceful degradation with automatic retry scheduling',
    duration: 30,
    failureType: 'rate-limit',
    connectorId: 'eia-api',
    expectedOutcome: 'Rate limit reached → Requests queued → Auto-retry after reset window → Service restored'
  },
  {
    id: 'scenario-3',
    name: 'Intermittent Timeout Handling',
    description: 'Inject random timeouts to test retry logic with jitter and backoff escalation',
    duration: 60,
    failureType: 'timeout',
    connectorId: 'bls-api',
    expectedOutcome: 'Random timeouts detected → Exponential backoff applied → Jitter prevents thundering herd → Service stabilizes'
  },
  {
    id: 'scenario-4',
    name: 'Authentication Failure and Token Refresh',
    description: 'Simulate expired auth token, trigger refresh workflow, and restore authenticated requests',
    duration: 25,
    failureType: 'auth',
    connectorId: 'usda-api',
    expectedOutcome: 'Auth failure detected → Token refresh attempted → New token acquired → Requests resume'
  },
  {
    id: 'scenario-5',
    name: 'Data Corruption Detection and Fallback',
    description: 'Inject malformed responses, trigger validation failures, and fall back to cached data',
    duration: 35,
    failureType: 'data-corruption',
    connectorId: 'eia-api',
    expectedOutcome: 'Invalid data detected → Quality checks fail → Fallback to last-known-good → Alert generated'
  },
  {
    id: 'scenario-6',
    name: 'Full Stack Recovery Test',
    description: 'Cascade multiple failure modes simultaneously and verify system-wide auto-remediation',
    duration: 90,
    failureType: 'intermittent',
    connectorId: 'all',
    expectedOutcome: 'Multiple connectors fail → Remediation jobs prioritized → Parallel recovery → All services restored'
  }
]

export function ConnectorTestSuite() {
  const [scenarios, setScenarios] = useState<TestScenario[]>(
    TEST_SCENARIOS.map(s => ({
      ...s,
      status: 'idle',
      steps: []
    }))
  )
  const [activeScenario, setActiveScenario] = useState<string | null>(null)
  const [remediationJobs, setRemediationJobs] = useState<RemediationJob[]>([])
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(true)

  useEffect(() => {
    if (!autoUpdateEnabled) return

    const interval = setInterval(() => {
      setRemediationJobs(autoRemediationService.getJobs())
    }, 1000)

    return () => clearInterval(interval)
  }, [autoUpdateEnabled])

  const runScenario = async (scenarioId: string) => {
    const scenario = scenarios.find(s => s.id === scenarioId)
    if (!scenario || scenario.status === 'running') return

    setActiveScenario(scenarioId)
    
    const steps: TestStep[] = [
      { id: 'init', name: 'Initialize test environment', status: 'pending' },
      { id: 'inject', name: `Inject ${scenario.failureType} failure`, status: 'pending' },
      { id: 'detect', name: 'Monitor failure detection', status: 'pending' },
      { id: 'circuit', name: 'Verify circuit breaker behavior', status: 'pending' },
      { id: 'remediate', name: 'Watch auto-remediation workflow', status: 'pending' },
      { id: 'recover', name: 'Validate service recovery', status: 'pending' },
      { id: 'verify', name: 'Verify data integrity post-recovery', status: 'pending' }
    ]

    updateScenario(scenarioId, { status: 'running', steps })

    toast.info(`Test Started: ${scenario.name}`, {
      description: 'Monitoring auto-remediation workflows...'
    })

    try {
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i]
        updateStep(scenarioId, step.id, { status: 'running', startTime: Date.now() })

        await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 3000))

        if (step.id === 'inject') {
          if (scenario.connectorId === 'all') {
            monitoringService.simulateAPIFailure('usda-api')
            monitoringService.simulateAPIFailure('eia-api')
            monitoringService.simulateAPIFailure('bls-api')
          } else {
            monitoringService.simulateAPIFailure(scenario.connectorId)
          }
          updateStep(scenarioId, step.id, { 
            status: 'completed', 
            endTime: Date.now(),
            details: `Injected ${scenario.failureType} failure into ${scenario.connectorId}`
          })
        } else if (step.id === 'circuit') {
          const health = monitoringService.getHealthStatus(scenario.connectorId)
          const circuitOpen = health?.circuitBreakerStatus === 'open'
          updateStep(scenarioId, step.id, { 
            status: circuitOpen ? 'completed' : 'failed', 
            endTime: Date.now(),
            details: circuitOpen 
              ? `Circuit breaker opened after ${health?.consecutiveFailures || 0} failures`
              : 'Circuit breaker did not open as expected'
          })
        } else if (step.id === 'remediate') {
          const jobsBefore = autoRemediationService.getJobs().length
          
          if (scenario.connectorId === 'all') {
            autoRemediationService.createRemediationJob('usda-api', 'USDA NASS API', 'manual-trigger')
            autoRemediationService.createRemediationJob('eia-api', 'EIA Data API', 'manual-trigger')
            autoRemediationService.createRemediationJob('bls-api', 'BLS Public Data API', 'manual-trigger')
          } else {
            autoRemediationService.createRemediationJob(
              scenario.connectorId, 
              scenario.connectorId.toUpperCase(), 
              'manual-trigger'
            )
          }
          
          const jobsAfter = autoRemediationService.getJobs().length
          const newJobs = jobsAfter - jobsBefore
          
          updateStep(scenarioId, step.id, { 
            status: 'completed', 
            endTime: Date.now(),
            details: `Created ${newJobs} remediation job(s) with exponential backoff strategy`
          })
        } else if (step.id === 'recover') {
          await new Promise(resolve => setTimeout(resolve, 5000))
          
          const activeJobs = autoRemediationService.getJobs()
            .filter(j => j.status === 'running' || j.status === 'pending')
          
          if (scenario.connectorId !== 'all') {
            monitoringService.simulateAPICall(scenario.connectorId)
          } else {
            monitoringService.simulateAPICall('usda-api')
            monitoringService.simulateAPICall('eia-api')
            monitoringService.simulateAPICall('bls-api')
          }
          
          updateStep(scenarioId, step.id, { 
            status: 'completed', 
            endTime: Date.now(),
            details: `Service recovered. ${activeJobs.length} job(s) still processing`
          })
        } else {
          updateStep(scenarioId, step.id, { 
            status: 'completed', 
            endTime: Date.now() 
          })
        }
      }

      updateScenario(scenarioId, { status: 'passed' })
      toast.success(`Test Passed: ${scenario.name}`, {
        description: 'Auto-remediation workflow completed successfully'
      })

    } catch (error) {
      updateScenario(scenarioId, { status: 'failed' })
      toast.error(`Test Failed: ${scenario.name}`, {
        description: error instanceof Error ? error.message : 'Unknown error'
      })
    } finally {
      setActiveScenario(null)
    }
  }

  const stopScenario = (scenarioId: string) => {
    updateScenario(scenarioId, { status: 'idle' })
    setActiveScenario(null)
    toast.info('Test stopped by user')
  }

  const resetScenario = (scenarioId: string) => {
    updateScenario(scenarioId, { status: 'idle', steps: [] })
  }

  const resetAll = () => {
    setScenarios(TEST_SCENARIOS.map(s => ({
      ...s,
      status: 'idle',
      steps: []
    })))
    setActiveScenario(null)
    autoRemediationService.clearCompletedJobs()
    toast.info('All tests reset')
  }

  const runAllSequentially = async () => {
    for (const scenario of scenarios) {
      if (scenario.status === 'idle') {
        await runScenario(scenario.id)
        await new Promise(resolve => setTimeout(resolve, 5000))
      }
    }
  }

  const updateScenario = (scenarioId: string, updates: Partial<TestScenario>) => {
    setScenarios(prev => prev.map(s => 
      s.id === scenarioId ? { ...s, ...updates } : s
    ))
  }

  const updateStep = (scenarioId: string, stepId: string, updates: Partial<TestStep>) => {
    setScenarios(prev => prev.map(s => {
      if (s.id !== scenarioId) return s
      return {
        ...s,
        steps: s.steps.map(step => 
          step.id === stepId ? { ...step, ...updates } : step
        )
      }
    }))
  }

  const getStatusIcon = (status: TestScenario['status']) => {
    switch (status) {
      case 'running':
        return <Pulse className="animate-pulse text-primary" weight="fill" />
      case 'passed':
        return <CheckCircle className="text-success" weight="fill" />
      case 'failed':
        return <XCircle className="text-danger" weight="fill" />
      default:
        return <Flask className="text-muted-foreground" />
    }
  }

  const getStepIcon = (status: TestStep['status']) => {
    switch (status) {
      case 'running':
        return <ChartLineUp className="animate-pulse text-primary" />
      case 'completed':
        return <CheckCircle className="text-success" weight="fill" />
      case 'failed':
        return <XCircle className="text-danger" weight="fill" />
      default:
        return <Clock className="text-muted-foreground" />
    }
  }

  const passedCount = scenarios.filter(s => s.status === 'passed').length
  const failedCount = scenarios.filter(s => s.status === 'failed').length
  const runningCount = scenarios.filter(s => s.status === 'running').length
  const totalTests = scenarios.length

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight flex items-center gap-3">
            <Bug className="text-primary" size={32} weight="fill" />
            Connector Failure Test Suite
          </h1>
          <p className="text-text-secondary mt-2 max-w-3xl">
            Comprehensive testing environment for connector failure scenarios and auto-remediation workflows.
            Watch the system detect failures, open circuit breakers, trigger remediation jobs, and restore service automatically.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Tests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-display font-bold">{totalTests}</div>
            <p className="text-xs text-text-muted mt-1">Test scenarios available</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle className="text-success" weight="fill" />
              Passed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-display font-bold text-success">{passedCount}</div>
            <Progress value={(passedCount / totalTests) * 100} className="mt-2 h-1" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <XCircle className="text-danger" weight="fill" />
              Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-display font-bold text-danger">{failedCount}</div>
            <Progress value={(failedCount / totalTests) * 100} className="mt-2 h-1" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Pulse className={cn("animate-pulse", runningCount > 0 ? "text-primary" : "text-muted-foreground")} weight="fill" />
              Running
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-display font-bold">{runningCount}</div>
            <p className="text-xs text-text-muted mt-1">Active test scenarios</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={runAllSequentially} disabled={runningCount > 0} size="lg">
          <Play weight="fill" />
          Run All Tests
        </Button>
        <Button onClick={resetAll} variant="outline" disabled={runningCount > 0}>
          <ArrowClockwise />
          Reset All
        </Button>
        <Separator orientation="vertical" className="h-8" />
        <div className="text-sm text-text-muted">
          {runningCount > 0 ? 'Tests in progress...' : 'Ready to test'}
        </div>
      </div>

      <Tabs defaultValue="scenarios" className="w-full">
        <TabsList>
          <TabsTrigger value="scenarios">Test Scenarios</TabsTrigger>
          <TabsTrigger value="remediation">
            Remediation Jobs
            {remediationJobs.filter(j => j.status === 'running' || j.status === 'pending').length > 0 && (
              <Badge variant="default" className="ml-2">
                {remediationJobs.filter(j => j.status === 'running' || j.status === 'pending').length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="logs">Execution Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="space-y-4 mt-6">
          {scenarios.map(scenario => (
            <Card key={scenario.id} className={cn(
              "border-2 transition-all",
              scenario.status === 'running' && "border-primary shadow-lg",
              scenario.status === 'passed' && "border-success/50",
              scenario.status === 'failed' && "border-danger/50"
            )}>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="mt-1">
                      {getStatusIcon(scenario.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-lg">{scenario.name}</CardTitle>
                      <CardDescription className="mt-1">{scenario.description}</CardDescription>
                      <div className="flex flex-wrap items-center gap-2 mt-3">
                        <Badge variant="outline" className="font-mono text-xs">
                          {scenario.connectorId}
                        </Badge>
                        <Badge variant="secondary">
                          {scenario.failureType}
                        </Badge>
                        <Badge variant="outline">
                          ~{scenario.duration}s
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {scenario.status === 'idle' && (
                      <Button 
                        onClick={() => runScenario(scenario.id)} 
                        disabled={activeScenario !== null}
                        size="sm"
                      >
                        <Play weight="fill" />
                        Run Test
                      </Button>
                    )}
                    {scenario.status === 'running' && (
                      <Button 
                        onClick={() => stopScenario(scenario.id)} 
                        variant="destructive"
                        size="sm"
                      >
                        <Stop weight="fill" />
                        Stop
                      </Button>
                    )}
                    {(scenario.status === 'passed' || scenario.status === 'failed') && (
                      <>
                        <Button 
                          onClick={() => runScenario(scenario.id)} 
                          disabled={activeScenario !== null}
                          variant="outline"
                          size="sm"
                        >
                          <ArrowClockwise />
                          Re-run
                        </Button>
                        <Button 
                          onClick={() => resetScenario(scenario.id)} 
                          variant="ghost"
                          size="sm"
                        >
                          Reset
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardHeader>

              {scenario.steps.length > 0 && (
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Wrench size={16} />
                      Test Execution Steps
                    </div>
                    <ScrollArea className="h-[240px] pr-4">
                      <div className="space-y-2">
                        {scenario.steps.map((step, index) => (
                          <div 
                            key={step.id} 
                            className={cn(
                              "flex items-start gap-3 p-3 rounded-lg border transition-all",
                              step.status === 'running' && "bg-primary/5 border-primary",
                              step.status === 'completed' && "bg-success/5 border-success/30",
                              step.status === 'failed' && "bg-danger/5 border-danger/30",
                              step.status === 'pending' && "bg-muted/20 border-border"
                            )}
                          >
                            <div className="flex items-center gap-2 min-w-0 flex-1">
                              <span className="text-xs font-mono text-muted-foreground w-8">
                                {index + 1}.
                              </span>
                              {getStepIcon(step.status)}
                              <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium">{step.name}</div>
                                {step.details && (
                                  <div className="text-xs text-muted-foreground mt-1">
                                    {step.details}
                                  </div>
                                )}
                                {step.startTime && step.endTime && (
                                  <div className="text-xs text-muted-foreground mt-1 font-mono">
                                    Duration: {((step.endTime - step.startTime) / 1000).toFixed(2)}s
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>

                  {scenario.status === 'passed' && (
                    <Alert className="mt-4 border-success/50 bg-success/5">
                      <CheckCircle className="text-success" weight="fill" />
                      <AlertTitle>Test Passed</AlertTitle>
                      <AlertDescription>
                        {scenario.expectedOutcome}
                      </AlertDescription>
                    </Alert>
                  )}

                  {scenario.status === 'failed' && (
                    <Alert className="mt-4 border-danger/50 bg-danger/5">
                      <Warning className="text-danger" weight="fill" />
                      <AlertTitle>Test Failed</AlertTitle>
                      <AlertDescription>
                        Expected: {scenario.expectedOutcome}
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              )}
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="remediation" className="space-y-4 mt-6">
          {remediationJobs.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Wrench size={48} className="text-muted-foreground mb-4" />
                <p className="text-text-secondary">No remediation jobs yet. Run a test to see auto-remediation in action.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {remediationJobs.map(job => (
                <Card key={job.id} className={cn(
                  "border-2",
                  job.status === 'running' && "border-primary",
                  job.status === 'success' && "border-success/50",
                  job.status === 'failed' && "border-danger/50"
                )}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        {job.status === 'running' && <Pulse className="animate-pulse text-primary" weight="fill" />}
                        {job.status === 'pending' && <Clock className="text-warning" />}
                        {job.status === 'success' && <CheckCircle className="text-success" weight="fill" />}
                        {job.status === 'failed' && <XCircle className="text-danger" weight="fill" />}
                        <div>
                          <CardTitle className="text-base">{job.sourceId}</CardTitle>
                          <CardDescription className="text-xs mt-1 font-mono">
                            {job.connectorId} • {job.reason.replace(/-/g, ' ')}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge variant={
                        job.status === 'success' ? 'default' :
                        job.status === 'running' ? 'secondary' :
                        job.status === 'failed' ? 'destructive' :
                        'outline'
                      }>
                        {job.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Attempts:</span>
                        <span className="font-mono">{job.attempts.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Current Backoff:</span>
                        <span className="font-mono">{(job.currentBackoffMs / 1000).toFixed(1)}s</span>
                      </div>
                      {job.nextRetryAt && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Next Retry:</span>
                          <span className="font-mono text-xs">{new Date(job.nextRetryAt).toLocaleTimeString()}</span>
                        </div>
                      )}
                      {job.totalDurationMs && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Total Duration:</span>
                          <span className="font-mono">{(job.totalDurationMs / 1000).toFixed(2)}s</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="logs" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Live Execution Logs</CardTitle>
              <CardDescription>Real-time monitoring of test execution and remediation workflows</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px] font-mono text-xs">
                <div className="space-y-1">
                  {scenarios.flatMap(s => 
                    s.steps
                      .filter(step => step.status !== 'pending')
                      .map(step => ({
                        scenarioName: s.name,
                        step,
                        timestamp: step.startTime || Date.now()
                      }))
                  ).sort((a, b) => b.timestamp - a.timestamp).map((log, index) => (
                    <div key={index} className="flex gap-3 py-1 hover:bg-muted/20 px-2 rounded">
                      <span className="text-muted-foreground shrink-0">
                        {log.step.startTime ? new Date(log.step.startTime).toLocaleTimeString() : '--:--:--'}
                      </span>
                      <span className={cn(
                        "shrink-0",
                        log.step.status === 'completed' && "text-success",
                        log.step.status === 'failed' && "text-danger",
                        log.step.status === 'running' && "text-primary"
                      )}>
                        [{log.step.status.toUpperCase()}]
                      </span>
                      <span className="text-muted-foreground shrink-0">{log.scenarioName}:</span>
                      <span>{log.step.name}</span>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
