# Connector Test Suite Documentation

## Overview

The **Connector Test Suite** is a comprehensive testing environment for validating connector failure scenarios and monitoring auto-remediation workflows in real-time. It provides an interactive interface to simulate various API failure conditions and observe how the system detects, responds to, and recovers from these failures automatically.

## Purpose

The test suite was created to:
- **Validate resilience**: Ensure the auto-remediation system can handle various failure modes
- **Test circuit breakers**: Verify circuit breakers open/close correctly under load
- **Monitor recovery workflows**: Watch exponential backoff and retry logic in action
- **Quality assurance**: Provide repeatable tests for system reliability
- **Demonstrate capabilities**: Show stakeholders how the system handles failures gracefully

## Test Scenarios

### 1. Circuit Breaker Opens After Consecutive Failures
**Duration**: ~45 seconds  
**Failure Type**: Network failures  
**Connector**: USDA API

**What it tests**:
- Injects 5 consecutive API failures
- Verifies circuit breaker opens after threshold
- Confirms auto-remediation job is created
- Watches exponential backoff recovery
- Validates connector restoration

**Expected outcome**: Circuit breaker opens → Auto-remediation triggered → Connector restored with exponential backoff

### 2. Rate Limit Exhaustion Recovery
**Duration**: ~30 seconds  
**Failure Type**: Rate limiting  
**Connector**: EIA API

**What it tests**:
- Simulates API rate limit exhaustion
- Verifies requests are queued gracefully
- Confirms retry scheduling respects reset window
- Validates service restoration after rate limit reset

**Expected outcome**: Rate limit reached → Requests queued → Auto-retry after reset window → Service restored

### 3. Intermittent Timeout Handling
**Duration**: ~60 seconds  
**Failure Type**: Random timeouts  
**Connector**: BLS API

**What it tests**:
- Injects random timeout errors
- Verifies jitter is applied to prevent thundering herd
- Confirms exponential backoff escalates properly
- Validates eventual service stabilization

**Expected outcome**: Random timeouts detected → Exponential backoff applied → Jitter prevents thundering herd → Service stabilizes

### 4. Authentication Failure and Token Refresh
**Duration**: ~25 seconds  
**Failure Type**: Auth token expiration  
**Connector**: USDA API

**What it tests**:
- Simulates expired authentication token
- Verifies token refresh workflow triggers
- Confirms new token acquisition
- Validates authenticated requests resume

**Expected outcome**: Auth failure detected → Token refresh attempted → New token acquired → Requests resume

### 5. Data Corruption Detection and Fallback
**Duration**: ~35 seconds  
**Failure Type**: Malformed responses  
**Connector**: EIA API

**What it tests**:
- Injects invalid/malformed API responses
- Verifies data validation catches corruption
- Confirms fallback to cached data
- Validates alert generation for data quality issues

**Expected outcome**: Invalid data detected → Quality checks fail → Fallback to last-known-good → Alert generated

### 6. Full Stack Recovery Test
**Duration**: ~90 seconds  
**Failure Type**: Multiple cascading failures  
**Connector**: All connectors

**What it tests**:
- Cascades failures across multiple connectors simultaneously
- Verifies remediation job prioritization
- Confirms parallel recovery workflows
- Validates system-wide restoration

**Expected outcome**: Multiple connectors fail → Remediation jobs prioritized → Parallel recovery → All services restored

## Test Execution Steps

Each test scenario follows a standardized 7-step execution flow:

### Step 1: Initialize Test Environment
- Prepares monitoring systems
- Resets circuit breaker states
- Clears previous test artifacts

### Step 2: Inject Failure
- Simulates the specified failure type
- Logs failure details for traceability
- Triggers connector degradation

### Step 3: Monitor Failure Detection
- Watches monitoring service detect the failure
- Confirms error counting and rate calculation
- Validates health status changes

### Step 4: Verify Circuit Breaker Behavior
- Checks if circuit breaker opens at threshold
- Validates circuit breaker state transitions
- Confirms failure count tracking

### Step 5: Watch Auto-Remediation Workflow
- Observes remediation job creation
- Monitors exponential backoff calculations
- Tracks retry attempts and timing

### Step 6: Validate Service Recovery
- Confirms successful API reconnection
- Verifies circuit breaker closes
- Validates health status restoration

### Step 7: Verify Data Integrity Post-Recovery
- Checks data quality after recovery
- Confirms no data loss occurred
- Validates all metrics are accurate

## Using the Test Suite

### Running a Single Test

1. Navigate to the **Test Suite** tab in the navigation
2. Find the test scenario you want to run
3. Click **"Run Test"** button
4. Watch the test execution in real-time
5. Review the results and step details

### Running All Tests

Click **"Run All Tests"** to execute all scenarios sequentially with automatic delays between tests.

### Stopping a Test

Click **"Stop"** on any running test to halt execution immediately.

### Resetting Tests

- **Reset Single**: Click "Reset" on a completed test to clear its results
- **Reset All**: Click "Reset All" to clear all test results and remediation jobs

## Test Results

### Status Indicators

- **Idle** (Flask icon): Test not yet run
- **Running** (Pulsing icon): Test currently executing
- **Passed** (Green checkmark): Test completed successfully
- **Failed** (Red X): Test did not meet expected criteria

### Metrics Dashboard

The dashboard shows real-time statistics:
- **Total Tests**: Number of available test scenarios
- **Passed**: Successfully completed tests
- **Failed**: Tests that did not meet criteria
- **Running**: Currently executing tests

### Step-by-Step Execution Log

Each test displays detailed step execution including:
- Step name and description
- Execution status
- Timing information
- Detailed outcome messages

## Remediation Jobs Tab

The **Remediation Jobs** tab shows all auto-remediation jobs created during tests:

- Job ID and connector information
- Current status (pending/running/success/failed)
- Number of retry attempts
- Current backoff delay
- Next retry timestamp
- Total duration

This provides transparency into the auto-remediation engine's behavior during failure recovery.

## Execution Logs Tab

The **Execution Logs** tab provides a chronological view of all test activities:
- Timestamp of each event
- Test scenario name
- Step execution status
- Real-time streaming of test progress

## Integration with Monitoring Systems

The test suite is fully integrated with:

1. **Data Quality Monitoring**: Test failures appear in the monitoring dashboard
2. **Auto-Remediation Service**: Tests trigger real remediation workflows
3. **Circuit Breaker System**: Tests respect actual circuit breaker logic
4. **Alert System**: Critical failures generate real alerts

## Best Practices

### For Testing
- Run individual tests first to understand behavior
- Use "Run All Tests" for comprehensive validation
- Review execution logs for debugging
- Reset tests between major system changes

### For Development
- Run tests after modifying connector code
- Use tests to validate new retry strategies
- Monitor remediation jobs for timing accuracy
- Check logs for unexpected behaviors

### For Demonstrations
- Tests showcase system resilience to stakeholders
- Real-time execution shows auto-healing capabilities
- Results prove reliability and fault tolerance
- Logs provide transparency and auditability

## Technical Implementation

### Failure Injection
```typescript
monitoringService.simulateAPIFailure(connectorId)
```
Injects consecutive failures into the monitoring system, triggering circuit breaker logic.

### Remediation Triggering
```typescript
autoRemediationService.createRemediationJob(
  connectorId,
  sourceId,
  'manual-trigger'
)
```
Creates a remediation job with exponential backoff and retry logic.

### Recovery Simulation
```typescript
monitoringService.simulateAPICall(connectorId)
```
Simulates successful API calls to restore connector health.

## Configuration

### Test Timeouts
Each step has variable timing (3-6 seconds) to simulate realistic conditions. Recovery steps include additional delays to allow remediation workflows to complete.

### Failure Patterns
Failure injection patterns are configurable per scenario:
- **Network failures**: 5 consecutive 503/504 errors
- **Rate limits**: Exhausted quota with reset window
- **Timeouts**: Random delays exceeding thresholds
- **Auth failures**: 401/403 responses
- **Data corruption**: Invalid JSON/schema violations

## Troubleshooting

### Test Never Completes
- Check if auto-remediation is enabled in settings
- Verify circuit breaker configuration
- Review browser console for errors

### Test Fails Unexpectedly
- Check remediation job logs for details
- Verify monitoring service is running
- Review step execution details for root cause

### Remediation Jobs Not Created
- Confirm auto-remediation is enabled
- Check if connector exists in system
- Verify failure threshold is reached

## Future Enhancements

Planned improvements include:
- Custom test scenario builder
- Performance benchmarking mode
- Export test results as reports
- Scheduled automated test runs
- Comparison with previous test runs
- Integration with CI/CD pipelines

## Related Documentation

- [Auto-Remediation Documentation](./AUTO_REMEDIATION_DOCUMENTATION.md)
- [Data Quality Monitoring](./DATA_QUALITY_MONITORING.md)
- [Monitoring Implementation](./MONITORING_IMPLEMENTATION.md)
- [API Integration Guide](./API_INTEGRATION_GUIDE.md)

## Support

For questions or issues with the test suite:
1. Review the execution logs for detailed error messages
2. Check the remediation jobs tab for workflow status
3. Consult related documentation for system configuration
4. Verify all prerequisites are met

The test suite is a powerful tool for validating system resilience and demonstrating the auto-healing capabilities of the Chronos platform.
