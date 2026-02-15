# Data Quality Monitoring Dashboard

## Overview

The Data Quality Monitoring Dashboard provides real-time visibility into API health, data freshness, and system reliability for Chronos. This feature enables proactive identification of data source issues, automated alerting for failures, and comprehensive tracking of data quality metrics.

## Purpose

As an evidence-driven platform, Chronos depends on accurate, timely data from multiple government APIs (BLS, EIA, USDA). The monitoring dashboard ensures:

1. **Transparency**: Users and administrators can see the health status of all data sources
2. **Reliability**: Automated alerts notify stakeholders of API failures or degraded performance
3. **Auditability**: Complete logs of all API calls, failures, and quality issues
4. **Trust**: Clear communication about data freshness and availability

## Key Features

### 1. System Health Overview

Four key performance indicators displayed prominently:

- **System Status**: Overall health (Healthy/Degraded/Critical) based on connector availability
- **Active Alerts**: Count of unacknowledged critical and warning alerts
- **Success Rate**: Percentage of successful API calls in the last 24 hours
- **Average Response Time**: Mean response time across all active connectors

### 2. Connector Health Cards

Each API connector displays:

- **Status Badge**: Healthy/Degraded/Offline with visual indicators
- **Circuit Breaker State**: Closed/Half-Open/Open
- **24h Uptime**: Availability percentage over 24 hours
- **Response Time**: Average response time in milliseconds
- **Error Count**: Number of failed requests in 24 hours
- **Rate Limit Status**: Current usage vs. limit
- **Quality Score**: Composite score (0-100) based on availability, performance, and data quality
- **Last Successful Fetch**: Timestamp of most recent successful data retrieval
- **Test Button**: Manual trigger to test the connector

### 3. Alert Management

Comprehensive alerting system with three severity levels:

#### Critical Alerts
- API connector offline (5+ consecutive failures)
- Circuit breaker open
- Data stale beyond critical threshold (>7 days)
- Error rate exceeds 30%

#### Warning Alerts
- Degraded performance (error rate 15-30%)
- Slow response times (>5 seconds sustained)
- Data approaching staleness threshold (>48 hours)
- Rate limit approaching capacity (>90%)

#### Info Alerts
- Scheduled maintenance windows
- Data revisions detected
- Configuration changes

**Alert Actions:**
- **Acknowledge**: Mark alert as seen (preserves in history)
- **Resolve**: Close alert and remove from active list
- **Action Items**: Each alert includes recommended remediation steps

### 4. Call History Log

Complete audit trail of API interactions:

- Request timestamp
- Endpoint called
- Response time
- HTTP status code
- Success/failure indicator
- Error messages (when applicable)
- Retry attempts

Logs are retained for 7 days by default (configurable).

### 5. Quality Scorecards

Per-connector quality metrics over selectable time periods (24h/7d/30d):

**Score Components:**
- **Availability**: Uptime percentage
- **Freshness**: Recency of data
- **Accuracy**: Error rate (inverse)
- **Completeness**: Data coverage
- **Consistency**: Variance in response patterns

**Overall Score**: Weighted composite (0-100)
- Availability: 35%
- Performance: 20%
- Freshness: 25%
- Quality: 20%

**Trend Direction**: Improving/Stable/Degrading based on consecutive measurements

**Recommendations**: Automated suggestions based on metrics (e.g., "Investigate frequent connection failures")

## Architecture

### Data Collection

**Simulated Monitoring Service** (`monitoring-service.ts`):
- Generates realistic health data for all connectors
- Maintains state in localStorage for persistence
- Provides subscription model for real-time updates
- Simulates API calls with success/failure patterns

**Production Integration Points** (for future real implementation):
- Hook into actual data connector calls
- Capture response times, status codes, payloads
- Validate data schemas and detect outliers
- Track rate limits and circuit breaker states

### Alert Rules Engine

Configurable rules with parameters:
- **Metric Type**: What to monitor (availability, response time, error rate, freshness)
- **Condition**: Threshold comparison (above/below/equals)
- **Threshold**: Numeric value triggering the alert
- **Duration**: How long condition must persist before alerting
- **Level**: Critical/Warning/Info
- **Cooldown**: Minimum time between repeat alerts
- **Notification Channels**: UI/Console/Persist

### Circuit Breaker Pattern

Protects against cascading failures:

1. **Closed**: Normal operation, requests flow through
2. **Open**: Connector has failed threshold times, requests blocked
3. **Half-Open**: Testing recovery, limited requests allowed

**Configuration per connector:**
- Failure threshold (default: 5 consecutive failures)
- Half-open test interval (default: 60 seconds)
- Success threshold to close (default: 2 consecutive successes)

### Data Persistence

**Local Storage Keys:**
- `chronos-monitoring-data`: Complete monitoring state
  - Health statuses
  - Alerts
  - Call logs (limited to 1000 entries)
  - Circuit breaker states
  - Rate limit tracking

**Retention Policies:**
- Alerts: 30 days (configurable)
- Call logs: 7 days (configurable)
- Metrics: Real-time with 30-second refresh

## User Workflows

### Administrator: Diagnosing API Failure

1. Navigate to **Data Quality** tab
2. Observe system status is "Critical"
3. Review active alerts showing "USDA AMS Connector Offline"
4. Click connector card to view details
5. Check call history for error patterns
6. Note circuit breaker is open
7. Review action items: "Check API endpoint status"
8. Acknowledge alert to track response
9. After resolution, mark alert as resolved

### Analyst: Verifying Data Freshness

1. Navigate to **Data Quality** tab
2. Scroll to connector health cards
3. Check "Last successful fetch" timestamps
4. Verify all critical sources updated within 24 hours
5. Review quality scorecards for any degradation trends
6. Export call logs for audit report

### User: Understanding Data Availability

1. See notice on main chart: "Data may be stale"
2. Click link to monitoring dashboard
3. View system health summary
4. Read active warning: "BLS API data stale (72 hours)"
5. Understand why recent data is not available
6. Check "Next scheduled refresh" estimate

## Configuration

Default monitoring configuration in `data-quality-monitoring.ts`:

```typescript
{
  refreshIntervalSeconds: 30,
  alertRetentionDays: 30,
  logRetentionDays: 7,
  enableNotifications: true,
  thresholds: {
    responseTimeWarningMs: 3000,
    responseTimeCriticalMs: 10000,
    errorRateWarning: 0.15,
    errorRateCritical: 0.30,
    dataFreshnessWarningHours: 48,
    dataFreshnessCriticalHours: 168,
    uptimeWarning: 0.95,
    uptimeCritical: 0.85,
  }
}
```

**Customization:**
- Adjust thresholds per data source type
- Configure alert routing (future: email, webhook)
- Set refresh schedules per connector
- Enable/disable individual alert rules

## Integration Points

### With Existing Features

1. **Source Registry**: Links to connector configurations and data provenance
2. **Data Sources View**: Shows last refresh status from monitoring
3. **Charts**: Display data freshness warnings when staleness detected
4. **Settings**: Configure monitoring preferences

### Future Enhancements

1. **Historical Metrics**: Store and visualize trends over weeks/months
2. **Comparative Analysis**: Compare connector reliability across periods
3. **Predictive Alerts**: ML-based anomaly detection
4. **External Notifications**: Email/SMS/webhook alerts
5. **SLA Tracking**: Measure against defined service level agreements
6. **Automated Remediation**: Self-healing for transient failures
7. **Custom Dashboards**: User-configurable monitoring views

## API Reference

### MonitoringService Methods

```typescript
// Get current health statuses for all connectors
getHealthStatuses(): APIHealthStatus[]

// Get health status for specific connector
getHealthStatus(connectorId: string): APIHealthStatus | undefined

// Get active alerts (optionally include acknowledged)
getAlerts(includeAcknowledged?: boolean): MonitoringAlert[]

// Get recent API call logs
getCallLogs(limit?: number): APICallLog[]

// Get system health summary
getSystemHealthSummary(): SystemHealthSummary

// Get quality scorecard for a source
getQualityScorecard(sourceId: string, period: '24h' | '7d' | '30d'): QualityScorecard

// Acknowledge an alert
acknowledgeAlert(alertId: string, userId?: string): void

// Resolve an alert
resolveAlert(alertId: string): void

// Manually trigger connector refresh
refreshConnector(connectorId: string): void

// Subscribe to monitoring updates
subscribe(callback: () => void): () => void
```

### Helper Functions

```typescript
// Calculate data staleness
calculateStaleness(
  lastDataPoint: string,
  expectedFrequency: 'hourly' | 'daily' | 'weekly' | 'monthly'
): { staleness: string; hoursStale: number }

// Calculate quality score
calculateQualityScore(metrics: QualityMetrics): number

// Evaluate alert rule
evaluateAlertRule(rule: AlertRule, currentValue: number, durationSeconds: number): boolean

// Format staleness for display
formatStaleness(hoursStale: number): string
```

## Accessibility

- **Keyboard Navigation**: Full tab/arrow key support
- **Screen Readers**: ARIA labels on all interactive elements
- **Color Independence**: Status conveyed via icons + text, not color alone
- **Focus Indicators**: High-contrast focus rings
- **Reduced Motion**: Respects `prefers-reduced-motion`

## Performance

- **Lazy Loading**: Call logs paginated (50 entries)
- **Efficient Updates**: Only re-render changed components
- **Debounced Refresh**: Auto-refresh throttled to 30-second intervals
- **Local Storage**: Minimal persistence overhead
- **Memory Management**: Call logs capped at 1000 entries

## Security

- **No Sensitive Data**: API keys never exposed to client
- **Read-Only UI**: Users cannot modify connector configurations
- **Audit Trail**: All alert actions logged with user ID
- **Rate Limiting**: Test refresh button throttled to prevent abuse

## Testing

Simulated scenarios for validation:

1. **Healthy System**: All connectors green, no alerts
2. **Degraded Connector**: 15-30% error rate, warning alert
3. **Offline Connector**: 5+ consecutive failures, critical alert, circuit open
4. **Slow Responses**: Response times >3000ms, performance warning
5. **Stale Data**: Last fetch >48 hours ago, freshness warning
6. **Rate Limit Approached**: Usage >90% of limit, info alert

## Compliance with Chronos Principles

✅ **Transparency**: All data quality issues visible to users
✅ **Auditability**: Complete history of API interactions
✅ **Evidence-Driven**: Metrics-based alerting, not subjective
✅ **Graceful Degradation**: System continues with stale data when APIs fail
✅ **User Education**: Clear explanations of what issues mean
✅ **No Hidden Failures**: API problems surfaced, not concealed

## Visual Design

Consistent with Chronos design system:

- **Dark Theme First**: High-contrast status indicators
- **Typography**: Font display for headers, font body for content
- **Colors**: Success (green), warning (yellow), danger (red), info (blue)
- **Spacing**: Generous padding, clear visual hierarchy
- **Animations**: Subtle pulse for active monitoring, spin for refresh
- **Icons**: Phosphor icons with consistent weight

## Deployment Notes

1. Initial state generated with random health data for demo
2. Replace simulated service with real API monitoring hooks
3. Configure alert notification endpoints (future)
4. Set up log aggregation for production (future)
5. Enable metrics export for external monitoring tools (future)

## Support & Documentation

- **User Guide**: In-app tooltips and help text
- **Admin Guide**: This document
- **API Docs**: Inline JSDoc comments in source
- **Troubleshooting**: Common issues and remediation steps in alerts
