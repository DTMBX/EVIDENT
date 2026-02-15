# API Integration Guide

## Overview

Chronos now integrates with real-world government data APIs to provide accurate, auditable economic data. This document describes the live API integrations, their endpoints, rate limits, and fallback strategies.

## Integrated APIs

### 1. Bureau of Labor Statistics (BLS) API

**Purpose**: Consumer Price Index (CPI) data and wage statistics

**Base URL**: `https://api.bls.gov/publicAPI/v2`

**Rate Limits**:
- 25 requests per minute
- 500 requests per hour
- Public API (no key required for basic access)

**Series IDs Used**:
- `CUUR0000SA0` - CPI All Items (US City Average)
- `CUUR0000SAF` - CPI Food
- `CUUR0000SA0E` - CPI Energy
- `CES0000000003` - Average Hourly Earnings

**Data Coverage**:
- CPI: 1913-present
- Wage data: 1964-present
- Monthly frequency
- National coverage

**Request Format**:
```json
{
  "seriesid": ["CUUR0000SA0"],
  "startyear": "2020",
  "endyear": "2024",
  "registrationkey": "PUBLIC"
}
```

**API Documentation**: https://www.bls.gov/developers/api_signature_v2.htm

**Limitations**:
- 10-year maximum date range per request (batched automatically)
- Response times can be slow during peak hours
- Historical revisions may occur

---

### 2. Energy Information Administration (EIA) API

**Purpose**: Petroleum, natural gas, and electricity price data

**Base URL**: `https://api.eia.gov/v2`

**Rate Limits**:
- 100 requests per minute
- 5,000 requests per hour
- Requires API key (DEMO_KEY for public access)

**Data Series**:

**Petroleum (eia-petroleum)**:
- `PET.EMM_EPM0_PTE_NUS_DPG.M` - Regular Gasoline Prices
- `PET.EMD_EPD2D_PTE_NUS_DPG.M` - Diesel Prices
- `PET.EMM_EPMRR_PTE_NUS_DPG.M` - Heating Oil Prices
- `PET.EER_EPPLLPA_PF4_Y35NY_DPG.M` - Propane Prices

**Natural Gas (eia-natural-gas)**:
- `NG.N3020US3.M` - Natural Gas Residential Prices

**Electricity (eia-electricity)**:
- `ELEC.PRICE.US-ALL.M` - Average Retail Electricity Prices

**Data Coverage**:
- Petroleum: 1990-present
- Natural Gas: 1967-present
- Electricity: 1990-present
- Monthly frequency
- National and regional coverage

**Request Format**:
```
GET /petroleum/data/?frequency=monthly&data[0]=value&start=2020-01&end=2024-12&api_key=DEMO_KEY
```

**API Documentation**: https://www.eia.gov/opendata/

**Limitations**:
- DEMO_KEY has lower rate limits
- State-level data may have gaps
- Units vary by series (gallons, therms, kWh)

---

### 3. USDA National Agricultural Statistics Service (NASS) API

**Purpose**: Agricultural commodity prices (dairy, meat, produce)

**Base URL**: `https://quickstats.nass.usda.gov/api`

**Rate Limits**:
- 60 requests per minute
- 1,000 requests per hour
- Requires API key (DEMO_KEY for public access)

**Commodities Tracked**:
- Dairy: Milk, Butter, Cheese
- Meat: Cattle (beef), Hogs (pork), Broilers (chicken)
- Produce: Apples, Potatoes, Tomatoes, Lettuce
- Grains: Corn, Wheat, Soybeans

**Data Coverage**:
- Historical: 1866-present (varies by commodity)
- Frequency: Monthly, quarterly, annual (varies)
- National and state-level coverage

**Request Format**:
```
GET /api_GET/?key=DEMO_KEY&commodity_desc=MILK&statisticcat_desc=PRICE RECEIVED&agg_level_desc=NATIONAL&format=JSON
```

**API Documentation**: https://quickstats.nass.usda.gov/api

**Limitations**:
- Complex parameter structure
- Inconsistent frequency across commodities
- "Price Received" is farm-gate, not retail
- Monthly data may be aggregated from quarterly

---

## Data Connector Architecture

### Connector Registry

All API connectors are registered in `src/lib/data-connectors.ts`:

```typescript
export const DATA_CONNECTORS: DataConnector[] = [
  {
    id: 'usda-ams-connector',
    sourceId: 'usda-ams',
    name: 'USDA AMS Dairy & Protein Connector',
    enabled: true,
    featureFlag: 'connector-usda-ams',
    retryConfig: {
      maxRetries: 3,
      backoffMs: 1000,
      circuitBreakerThreshold: 5,
    },
    rateLimit: {
      requestsPerMinute: 60,
      requestsPerHour: 1000,
    },
    allowedDomains: ['ams.usda.gov', 'marketnews.usda.gov'],
  },
  // ... more connectors
]
```

### API Clients

Each API has a dedicated client class in `src/lib/api-clients.ts`:

- `BLSAPIClient` - Bureau of Labor Statistics
- `EIAAPIClient` - Energy Information Administration
- `USDAAPIClient` - USDA NASS QuickStats

### Rate Limiting

Built-in rate limiter enforces per-connector limits:

```typescript
class RateLimiter {
  constructor(
    private requestsPerMinute: number,
    private requestsPerHour: number
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // Queue and throttle requests
  }
}
```

### Retry Strategy

All API calls use exponential backoff:

1. Initial attempt
2. Wait `backoffMs` (1-2 seconds depending on API)
3. Retry up to `maxRetries` (typically 3)
4. Circuit breaker trips after `circuitBreakerThreshold` consecutive failures

### Timeout Protection

All requests have configurable timeouts (default 30 seconds) using `AbortController`.

---

## Fallback Strategy

When real API data is unavailable, the system falls back gracefully:

### Level 1: Primary API
Try to fetch from the configured real-world API.

### Level 2: Simulated Data
If API fails, generate deterministic simulated data based on:
- Historical base prices
- Trend growth (~0.3% monthly)
- Random variation (±5%)
- Consistent with item characteristics

### Level 3: Error State
If all fallbacks fail, surface clear error messages to the user with:
- Last successful fetch timestamp
- Reason for failure
- Expected next retry time

### User Experience

Users see:
- ✅ **Live data badge** when using real API data
- ⚠️ **Simulated data badge** when using fallback
- 🔄 **Last updated** timestamp
- 🛑 **Error state** with retry option

---

## Data Quality Pipeline

### 1. Raw Data Ingestion
```typescript
interface RawPricePoint {
  id: string
  itemId: string
  date: string
  region: string
  value: number
  unit: UnitStandard
  sourceId: string
  retrievalTimestamp: string
  sourceUrl: string
  checksumHash?: string
}
```

### 2. Validation
- Schema validation (required fields)
- Unit validation (matches item standard)
- Negative value checks
- Duplicate detection
- Sudden jump detection (>50% change)

### 3. Normalization
- Unit conversion to standard units
- Frequency alignment (monthly)
- Outlier detection (robust z-score)
- Confidence scoring

### 4. Storage
- Raw data preserved immutably
- Normalized data with QA flags
- Version tracking for revisions

---

## Series Mapping

### Item ID → API Series

The system maintains mappings from internal item IDs to external API series:

**BLS CPI Series**:
- `cpi-all-items` → `CUUR0000SA0`
- `cpi-food` → `CUUR0000SAF`
- `cpi-energy` → `CUUR0000SA0E`

**EIA Petroleum Series**:
- `gasoline-gallon` → `PET.EMM_EPM0_PTE_NUS_DPG.M`
- `diesel-gallon` → `PET.EMD_EPD2D_PTE_NUS_DPG.M`
- `heating-oil-gallon` → `PET.EMM_EPMRR_PTE_NUS_DPG.M`
- `propane-gallon` → `PET.EER_EPPLLPA_PF4_Y35NY_DPG.M`

**USDA NASS Commodities**:
- `milk-gallon` → `MILK`
- `eggs-dozen` → `EGGS`
- `butter-lb` → `BUTTER`
- `cheese-lb` → `CHEESE`
- `ground-beef-lb` → `CATTLE`
- `chicken-breast-lb` → `BROILERS`

---

## Usage Examples

### Fetching Data for a Single Item

```typescript
import { fetchSeries, DATA_CONNECTORS } from '@/lib/data-connectors'

const connector = DATA_CONNECTORS.find(c => c.sourceId === 'bls-cpi')

const response = await fetchSeries(connector, {
  region: 'US-National',
  itemId: 'cpi-all-items',
  dateRange: {
    start: '2020-01-01',
    end: '2024-12-31',
  },
})

console.log(`Fetched ${response.metadata.recordCount} points`)
console.log(`Coverage: ${response.metadata.coverage}%`)
```

### Validating and Normalizing Data

```typescript
import { validateRawData, normalizePriceData } from '@/lib/data-connectors'

const validation = validateRawData(response.rawPoints)

if (validation.passed) {
  const normalized = normalizePriceData(response.rawPoints, validation)
  console.log(`Normalized ${normalized.normalizedData.length} points`)
}
```

### Computing Confidence Scores

```typescript
import { computeConfidenceScore } from '@/lib/data-connectors'

const source = {
  reliabilityTier: 'tier-1' as const,
}

const confidence = computeConfidenceScore(
  'cpi-all-items',
  normalized.normalizedData,
  source
)

console.log(`Confidence: ${confidence.score}/100`)
```

---

## API Key Management

### Demo Keys (Default)

The application ships with public demo keys:
- BLS: `PUBLIC` (no key required)
- EIA: `DEMO_KEY`
- USDA: `DEMO_KEY`

### Production Keys

For production deployments, register for free API keys:

**BLS Registration**:
https://data.bls.gov/registrationEngine/

**EIA Registration**:
https://www.eia.gov/opendata/register.php

**USDA Registration**:
https://quickstats.nass.usda.gov/api

### Key Storage

Store keys securely server-side (never expose in client code):

```typescript
// ❌ NEVER DO THIS
const API_KEY = 'abc123...'

// ✅ DO THIS
const API_KEY = process.env.EIA_API_KEY || 'DEMO_KEY'
```

**Note**: This is a client-side PWA application. API keys are currently exposed in requests. For production use, implement a server-side proxy to secure API keys.

---

## Monitoring and Observability

### Health Checks

Each connector tracks:
- `lastSuccessfulFetch` timestamp
- `lastError` message
- Circuit breaker state
- Request queue depth

### Metrics to Monitor

1. **Request Success Rate**: % of successful API calls
2. **Response Time**: p50, p95, p99 latencies
3. **Coverage**: % of requested date range with data
4. **Confidence Score**: Weighted data quality metric
5. **Fallback Rate**: % of requests using simulated data

### Alerts

Set up alerts for:
- Circuit breaker open (5+ consecutive failures)
- Coverage below 80%
- Confidence score below 70
- Fallback rate above 20%

---

## Testing

### Unit Tests

Test individual API clients:

```typescript
import { blsClient } from '@/lib/api-clients'

describe('BLSAPIClient', () => {
  it('fetches CPI data correctly', async () => {
    const data = await blsClient.fetchSeries({
      seriesId: 'CUUR0000SA0',
      startYear: '2020',
      endYear: '2021',
    })
    expect(data.length).toBeGreaterThan(0)
  })
})
```

### Integration Tests

Test full data pipeline:

```typescript
import { fetchSeries, validateRawData, normalizePriceData } from '@/lib/data-connectors'

describe('Data Pipeline', () => {
  it('fetches, validates, and normalizes data', async () => {
    const connector = DATA_CONNECTORS[0]
    const response = await fetchSeries(connector, request)
    const validation = validateRawData(response.rawPoints)
    const normalized = normalizePriceData(response.rawPoints, validation)
    
    expect(normalized.normalizedData.length).toBeGreaterThan(0)
    expect(validation.errors.length).toBe(0)
  })
})
```

---

## Future Enhancements

### Planned Integrations

1. **FRED API** (Federal Reserve Economic Data)
   - Housing price indices
   - Unemployment rates
   - Interest rates

2. **Census Bureau API**
   - Regional wage data
   - Demographic statistics

3. **State & Local APIs**
   - State minimum wage laws
   - Regional CPI adjustments

### Optimization Opportunities

1. **Caching Layer**: Redis/IndexedDB for frequently accessed series
2. **Batch Requests**: Combine multiple item requests
3. **WebSocket Streaming**: Real-time updates for recent data
4. **Edge Computing**: Deploy connectors closer to API sources

---

## Troubleshooting

### Common Issues

**"API request timeout"**
- Increase `timeoutMs` in client config
- Check network connectivity
- Verify API service status

**"Rate limit exceeded"**
- Reduce request frequency
- Implement better caching
- Upgrade to registered API key (higher limits)

**"No data returned from API"**
- Verify series ID is correct
- Check date range is within API coverage
- Confirm API hasn't deprecated the series

**"Falling back to simulated data"**
- Check API key validity
- Verify internet connection
- Review API status pages

### API Status Pages

- BLS: https://www.bls.gov/bls/news.htm
- EIA: https://www.eia.gov/about/statusmessages.php
- USDA: https://www.usda.gov/

---

## Compliance

### Terms of Service

All integrated APIs are U.S. government public data sources with permissive terms:

- **BLS**: Public domain, no attribution required
- **EIA**: Public domain, attribution requested
- **USDA**: Public domain, attribution requested

### Attribution

The application displays attribution in:
- Source Registry view
- Exported datasets
- Methodology documentation
- Chart footnotes

### Data Licensing

All data is provided "as-is" without warranties. Users are responsible for verifying data accuracy for their use cases.

---

## Support

For API-specific questions:
- BLS: https://data.bls.gov/cgi-bin/forms/bls_mail
- EIA: infoctr@eia.gov
- USDA: nassrfohelpdesk@usda.gov

For Chronos integration issues:
- Review this documentation
- Check error logs
- File an issue with reproduction steps
