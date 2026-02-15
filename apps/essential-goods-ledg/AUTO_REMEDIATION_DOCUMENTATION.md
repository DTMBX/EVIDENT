# Automated Remediation Workflows

## Overview

The Automated Remediation system provides intelligent, self-healing capabilities for data connector failures in Chronos. When API connectors experience failures, the system automatically attempts to restore service using exponential backoff retry strategies, circuit breaker patterns, and configurable remediation policies.

## Purpose

As an evidence-driven platform dependent on multiple external government APIs (BLS, EIA, USDA, FRED), Chronos must maintain high availability and data freshness. The automated remediation system ensures:

1. **Resilience**: Automatic recovery from transient failures
2. **Transparency**: Complete audit trail of all remediation attempts
3. **Control**: Configurable retry policies and manual overrides
4. **Efficiency**: Intelligent backoff prevents API rate limit exhaustion
5. **Visibility**: Real-time monitoring of recovery workflows

## Key Features

### 1. Exponential Backoff Retry Strategy

The system uses exponential backoff to retry failed connector requests with progressively longer delays between attempts:

```
Attempt 1: Initial backoff (default: 1000ms)
Attempt 2: Initial × Multiplier¹ (default: 2000ms)
Attempt 3: Initial × Multiplier² (default: 4000ms)
Attempt 4: Initial × Multiplier³ (default: 8000ms)
Attempt 5: Initial × Multiplier⁴ (default: 16000ms)
```

**Key Parameters:**
- **Initial Backoff**: Starting delay in milliseconds (default: 1000ms)
- **Backoff Multiplier**: Exponential growth factor (default: 2x)
- **Max Backoff**: Upper limit on delay (default: 60000ms = 1 minute)
- **Max Retries**: Maximum number of attempts (default: 5)

### 2. Jitter Addition

To prevent thundering herd problems when multiple connectors fail simultaneously, the system adds randomized jitter to backoff delays:

```
Final Delay = Calculated Backoff + Random(0, Jitter Max)
```

**Configuration:**
- **Jitter Enabled**: Toggle jitter on/off (default: enabled)
- **Jitter Max**: Maximum random delay to add (default: 500ms)

### 3. Circuit Breaker Integration

The remediation system works in tandem with circuit breakers to prevent cascading failures:

**Circuit Breaker States:**
- **Closed**: Normal operation, requests flow through
- **Half-Open**: Testing if service has recovered
- **Open**: Service unavailable, requests immediately fail

**Auto-Remediation Triggers:**
- Circuit breaker transitions to **Open** state (5+ consecutive failures)
- Error rate exceeds 30% over 24-hour window
- Manual trigger by administrator

### 4. Remediation Job Lifecycle

Each remediation workflow is tracked as a discrete job with the following states:

**Job States:**
- **Pending**: Scheduled for execution, waiting for next retry window
- **Running**: Currently attempting to restore connector
- **Success**: Connector restored to healthy state
- **Failed**: Max retries exhausted without recovery
- **Cancelled**: Manually stopped by administrator

**Job Properties:**
- Unique ID and timestamp
- Connector and source identifiers
- Failure reason (circuit breaker, high error rate, consecutive failures)
- Attempt history with timestamps and delays
- Total duration and final outcome

### 5. Configuration Options

#### Global Settings

**Core Configuration:**
- **Auto-Remediation Enabled**: Master toggle (default: enabled)
- **Notifications Enabled**: Toast notifications for job events (default: enabled)
- **Circuit Breaker Auto-Retry**: Automatically retry open circuit breakers (default: enabled)
- **Circuit Breaker Retry Interval**: How often to check for open circuits (default: 300000ms = 5 minutes)

**Retry Policy:**
- **Max Retries**: Number of attempts before giving up (range: 1-10, default: 5)
- **Initial Backoff**: Starting delay in milliseconds (range: 500-5000ms, default: 1000ms)
- **Max Backoff**: Maximum delay cap in milliseconds (range: 10000-300000ms, default: 60000ms)
- **Backoff Multiplier**: Exponential growth rate (range: 1.5-3x, default: 2x)
- **Jitter Enabled**: Add randomness to prevent collisions (default: enabled)
- **Jitter Max**: Maximum random delay to add (range: 0-1000ms, default: 500ms)

#### Per-Connector Configuration

Each data connector has its own retry configuration stored in the connector definition:

```typescript
{
  retryConfig: {
    maxRetries: 3,
    backoffMs: 1000,
    circuitBreakerThreshold: 5
  }
}
```

### 6. Manual Operations

**Job Management:**
- **Cancel Job**: Stop a pending or running remediation job
- **Retry Job**: Re-attempt a failed or cancelled job
- **Clear Completed**: Remove successful/failed/cancelled jobs from view

**Connector Actions:**
- **Test Connector**: Manually trigger a test request
- **Force Refresh**: Bypass auto-refresh schedule and fetch immediately
- **Reset Circuit Breaker**: Manually close an open circuit breaker

## Workflow Architecture

### Automatic Remediation Flow

```
1. Monitoring Service detects failure
   ↓
2. Checks if auto-remediation is enabled
   ↓
3. Checks if active job already exists for connector
   ↓
4. Creates new RemediationJob with reason
   ↓
5. Executes first attempt immediately
   ↓
6. If failure:
   a. Calculate exponential backoff
   b. Add jitter if enabled
   c. Schedule next retry
   d. Update job state to "pending"
   ↓
7. Retry loop continues until:
   - Success: Connector healthy → Job "success"
   - Max retries: Exhausted attempts → Job "failed"
   - Cancel: Manual intervention → Job "cancelled"
```

### Circuit Breaker Monitoring Loop

```
Every N milliseconds (default: 300000ms = 5 min):
  For each connector:
    If circuit breaker is OPEN:
      If no active remediation job exists:
        Create new remediation job
```

### Remediation Attempt Execution

```
1. Set job status to "running"
2. Wait for calculated backoff delay (except first attempt)
3. Simulate/Execute API call to connector
4. Wait for response
5. Check connector health status
6. Record attempt result with:
   - Success/failure
   - Response time
   - Error message (if any)
   - Timestamp
7. If success:
   - Set job status to "success"
   - Record total duration
   - Send success notification
8. If failure:
   - Check retry count against max retries
   - If exhausted: Set job status to "failed"
   - If retries remain: Calculate next backoff, schedule retry
```

## Implementation Details

### Core Service: `AutoRemediationService`

**Location**: `/src/lib/auto-remediation.ts`

**Key Methods:**

```typescript
// Configuration
getConfig(): RemediationConfig
updateConfig(updates: Partial<RemediationConfig>): void

// Job Management
createRemediationJob(connectorId, sourceId, reason): RemediationJob
executeJob(jobId): Promise<void>
cancelJob(jobId): void
retryJob(jobId): void
clearCompletedJobs(): void

// Queries
getJobs(): RemediationJob[]
getJob(jobId): RemediationJob | undefined
getActiveJobsForConnector(connectorId): RemediationJob[]
getStats(): RemediationStats

// Reactivity
subscribe(callback): () => void (returns unsubscribe function)
```

**Internal Methods:**

```typescript
calculateBackoff(attemptNumber, baseBackoff): number
scheduleRetry(job): void
startCircuitBreakerMonitoring(): void
```

### React Component: `AutoRemediationView`

**Location**: `/src/components/AutoRemediationView.tsx`

**Features:**
- Real-time job status display
- Configuration panel with sliders and toggles
- Active and completed job lists
- Per-job detail expansion with attempt history
- Manual job controls (cancel, retry, clear)
- Statistics dashboard (success rate, avg attempts, avg duration)

**Component Hierarchy:**
```
AutoRemediationView
├── Statistics Cards (Total, Success Rate, Avg Attempts, Avg Duration)
├── Configuration Card (collapsible)
│   ├── Toggle switches (enabled, notifications, circuit breaker, jitter)
│   └── Range sliders (max retries, multiplier, backoffs)
├── Active Jobs Card
│   └── RemediationJobCard × N (for each active job)
└── Completed Jobs Card
    └── RemediationJobCard × N (for each completed job)
```

### Data Persistence

**Storage Keys:**
- `chronos-remediation-config`: Global configuration
- `chronos-remediation-jobs`: Job history (up to 1000 recent jobs)

**Storage Strategy:**
- LocalStorage for configuration and job history
- In-memory state for active timers and subscriptions
- Restoration on page reload: pending jobs are rescheduled

### Integration Points

**1. Monitoring Service Integration**

The remediation service subscribes to monitoring events and creates jobs based on connector health:

```typescript
monitoringService.subscribe(() => {
  const healthStatuses = monitoringService.getHealthStatuses()
  healthStatuses.forEach(health => {
    if (shouldCreateRemediationJob(health)) {
      autoRemediationService.createRemediationJob(...)
    }
  })
})
```

**2. Data Connector Integration**

Remediation jobs execute test calls via the monitoring service:

```typescript
monitoringService.simulateAPICall(connectorId)
```

In production, this would call the actual connector fetch method:

```typescript
await fetchSeries(connector, request)
```

**3. Toast Notification Integration**

Success, failure, and status updates trigger user notifications:

```typescript
toast.success("Connector restored: BLS CPI")
toast.error("Remediation failed after 5 attempts")
toast.info("Auto-remediation started for USDA NASS")
```

## Best Practices

### Configuration Recommendations

**Conservative (High-Value APIs):**
- Max Retries: 3-5
- Initial Backoff: 2000ms
- Max Backoff: 120000ms (2 minutes)
- Backoff Multiplier: 2.5x
- Jitter: Enabled

**Aggressive (Tolerant APIs):**
- Max Retries: 5-10
- Initial Backoff: 500ms
- Max Backoff: 30000ms (30 seconds)
- Backoff Multiplier: 1.5x
- Jitter: Enabled

**Rate-Limited APIs:**
- Max Retries: 3
- Initial Backoff: 5000ms
- Max Backoff: 300000ms (5 minutes)
- Backoff Multiplier: 3x
- Jitter: Enabled

### Operational Considerations

**Monitoring:**
- Review success rate weekly (target: >80%)
- Investigate patterns in failed jobs
- Adjust retry policies based on API behavior

**Alerting:**
- Set up external alerts for sustained failures (>24 hours)
- Monitor jobs that repeatedly fail and retry
- Track "flapping" connectors (rapid success/failure cycles)

**Maintenance:**
- Periodically clear completed jobs (retention: 7-30 days)
- Archive long-term remediation statistics
- Document per-connector reliability characteristics

## Security Considerations

**API Key Protection:**
- Remediation retries never expose API keys in logs
- All connector credentials remain server-side only
- Job history does not store sensitive payloads

**Rate Limit Respect:**
- Exponential backoff prevents API abuse
- Jitter prevents coordinated retry storms
- Manual cancel ensures escape hatch for runaway jobs

**Audit Trail:**
- Complete history of all remediation attempts
- Timestamps and durations for compliance auditing
- Reason codes for forensic analysis

## Performance Characteristics

**Memory Usage:**
- ~1KB per job in history
- Max 1000 jobs retained = ~1MB
- Minimal overhead for active jobs (<10KB)

**CPU Usage:**
- Negligible except during active retry attempts
- Timer-based scheduling (no polling)
- Efficient reactivity with subscription model

**Storage:**
- LocalStorage: ~1-2MB for full history
- No server-side storage required
- Automatic pruning of old jobs

## Future Enhancements

**Potential Improvements:**
- Machine learning-based backoff optimization
- Per-connector failure pattern detection
- Automated escalation to manual review
- Webhook notifications for critical failures
- Integration with external monitoring services (PagerDuty, Datadog)
- Historical success rate trending and prediction
- A/B testing different retry strategies
- Auto-tuning based on observed API behavior

## Acceptance Criteria

**MUST:**
- ✅ Support exponential backoff with configurable parameters
- ✅ Integrate with circuit breaker pattern
- ✅ Provide complete audit trail of all attempts
- ✅ Allow manual cancellation and retry
- ✅ Display real-time job status
- ✅ Respect API rate limits via backoff
- ✅ Add jitter to prevent thundering herd
- ✅ Auto-trigger on circuit breaker open events
- ✅ Persist configuration across sessions

**SHOULD:**
- ✅ Show statistics (success rate, avg attempts, duration)
- ✅ Provide detailed attempt history per job
- ✅ Enable/disable auto-remediation globally
- ✅ Allow per-job detail inspection
- ✅ Clear completed jobs in bulk

**COULD:**
- Future: ML-based optimization
- Future: External monitoring integrations
- Future: Slack/email notifications
- Future: Connector-specific retry policies in UI

## Related Documentation

- [Data Quality Monitoring](./DATA_QUALITY_MONITORING.md)
- [API Integration Guide](./API_INTEGRATION_GUIDE.md)
- [Data Pipeline Implementation](./DATA_PIPELINE_IMPLEMENTATION.md)
- [Monitoring Implementation](./MONITORING_IMPLEMENTATION.md)
