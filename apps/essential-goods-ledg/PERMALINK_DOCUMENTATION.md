# Shareable Permalink Feature Documentation

## Overview

The shareable permalink feature allows users to generate permanent URLs that encode complete analytics configurations. This enables reproducible analysis, citation-ready URLs for research and reporting, and seamless sharing of specific analytical views.

## Key Features

### 1. Configuration Encoding
All analytics configuration parameters are encoded into a URL-safe base64 string containing:
- Region selection
- Date range (start and end dates)
- Base date for index calculations
- Wage type (minimum or median)
- Basket item IDs
- Metric mode (nominal, real, or hours-of-work)
- Verdict threshold
- Event window (in months)

### 2. Tamper-Evident Hash
Each configuration generates a unique hash that can be:
- Included in research documentation
- Used to verify configuration integrity
- Referenced in published papers and reports
- Validated against the original configuration

### 3. Automatic Loading
When a user accesses a permalink URL:
- Configuration is automatically decoded from the URL parameter
- Analytics view loads with the exact saved state
- An alert banner indicates the configuration source
- All visualizations reflect the permalink parameters

### 4. Configuration Immutability
- Permalinks represent a point-in-time configuration
- Original permalink remains unchanged
- Modifications create a new configuration state
- Users can generate new permalinks from modified states

## Usage Guide

### Generating a Permalink

1. Navigate to the Analytics tab
2. Configure your analysis:
   - Select region
   - Choose wage type
   - Set metric mode
   - Adjust date range
   - Configure other parameters
3. Click "Share Configuration" button
4. Copy the permalink URL from the dialog
5. Note the configuration hash for documentation

### Sharing a Permalink

Include the full URL in:
- Research papers (footnotes or references)
- Email communications
- Documentation
- Social media posts
- Presentations

Example URL structure:
```
https://yourdomain.com/?config=eyJjb25maWciOnsiZ...&hash=#analytics
```

### Using a Shared Permalink

1. Click or paste the permalink URL
2. Analytics view loads automatically
3. Alert banner confirms permalink-loaded state
4. View matches the sender's exact configuration
5. Make modifications to create your own analysis

## Technical Implementation

### Encoding Algorithm

```typescript
const data: PermalinkData = {
  config: AnalyticsConfig,
  created: ISO8601 timestamp,
  version: "1.0"
}

// Serialize to JSON
const json = JSON.stringify(data)

// Encode for URL safety
const encoded = btoa(encodeURIComponent(json))
```

### Decoding Algorithm

```typescript
// Decode from URL-safe format
const json = decodeURIComponent(atob(encoded))

// Parse JSON
const data: PermalinkData = JSON.parse(json)

// Extract configuration
return data.config
```

### Hash Generation

Simple deterministic hash of configuration JSON for integrity verification:

```typescript
function generatePermalinkHash(config: AnalyticsConfig): string {
  const json = JSON.stringify(config)
  let hash = 0
  
  for (let i = 0; i < json.length; i++) {
    const char = json.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  
  return Math.abs(hash).toString(16).padStart(8, '0')
}
```

## Best Practices

### For Researchers
- **Always include the configuration hash** in your methodology section
- **Document the permalink creation date** for audit trails
- **Archive the full URL** in supplementary materials
- **Verify the link works** before publication
- **Consider URL shorteners** for print publications (but keep full URL in digital versions)

### For Journalists
- Include permalinks in article footnotes or data sources sections
- Archive permalinks with story documentation
- Use configuration hash in corrections or updates
- Share permalinks with fact-checkers and editors

### For Educators
- Include permalinks in course materials
- Share with students for reproducible examples
- Use in assignment instructions for consistent datasets
- Archive for future course iterations

### For Policymakers
- Reference permalinks in policy briefs
- Include in testimony documentation
- Share with stakeholders for transparency
- Use in public communications for verification

## Configuration Parameters Reference

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `region` | string | Geographic region | "US-National" |
| `dateRange.start` | string (ISO 8601) | Analysis start date | "2021-01-01" |
| `dateRange.end` | string (ISO 8601) | Analysis end date | "2024-01-01" |
| `baseDate` | string (ISO 8601) | Index base date | "2021-01-01" |
| `wageType` | "minimum" \| "median" | Wage series type | "minimum" |
| `basketItemIds` | string[] | Item IDs in basket | ["eggs-dozen", "milk-gallon"] |
| `metricMode` | "nominal" \| "real" \| "hours-of-work" | Metric display mode | "hours-of-work" |
| `verdictThreshold` | number | Affordability verdict threshold | 1.00 |
| `eventWindowMonths` | number | Event study window size | 3 |

## URL Structure

### Components

```
https://domain.com/?config={BASE64_ENCODED_CONFIG}#analytics
```

- **Base URL**: Your application domain
- **Query parameter**: `config` contains encoded configuration
- **Hash fragment**: `#analytics` triggers analytics tab navigation

### Example

```
https://egl.example.com/?config=eyJjb25maWciOnsicmVnaW9uIjoiVVMtTmF0aW9uYWwiLCJkYXRlUmFuZ2UiOnsic3RhcnQiOiIyMDIxLTAxLTAxIiwiZW5kIjoiMjAyNC0wMS0wMSJ9LCJiYXNlRGF0ZSI6IjIwMjEtMDEtMDEiLCJ3YWdlVHlwZSI6Im1pbmltdW0iLCJiYXNrZXRJdGVtSWRzIjpbImVnZ3MtZG96ZW4iLCJtaWxrLWdhbGxvbiJdLCJtZXRyaWNNb2RlIjoiaG91cnMtb2Ytd29yayIsInZlcmRpY3RUaHJlc2hvbGQiOjEsImV2ZW50V2luZG93TW9udGhzIjozfSwiY3JlYXRlZCI6IjIwMjQtMDEtMTVUMTA6MzA6MDBaIiwidmVyc2lvbiI6IjEuMCJ9#analytics
```

## Security Considerations

### Safe Practices
- Permalinks contain only analysis configuration, no user data
- No authentication credentials in URLs
- Configuration parameters are validated on load
- Malformed configurations gracefully degrade

### Privacy
- No personally identifiable information in permalinks
- No tracking or analytics via permalink parameters
- Configurations are client-side only
- No server-side permalink storage required

## Error Handling

### Invalid Permalink
If a permalink cannot be decoded:
- Application shows error toast
- Falls back to default configuration
- Logs error for debugging

### Version Mismatch
If permalink version differs from current:
- Attempts backward-compatible decode
- Warns user of potential incompatibility
- Offers to create new permalink with current version

### Missing Parameters
If decoded configuration is incomplete:
- Fills missing parameters with sensible defaults
- Logs warning for debugging
- User can regenerate complete permalink

## Future Enhancements

### Potential Additions
- **Short URL service** integration for easier sharing
- **QR code generation** for print materials
- **Permalink history** tracking in user profile
- **Permalink collections** for related analyses
- **Expiration dates** for time-sensitive configurations
- **Permalink analytics** to track usage (opt-in)
- **Collaborative annotations** on shared permalinks

## Changelog

### Version 1.0 (Current)
- Initial implementation
- Base64 URL encoding
- Configuration hash generation
- Automatic loading from URL
- Share dialog with copy-to-clipboard
- Alert banner for permalink-loaded state
