# Wage vs Essentials Analytics Module - Implementation Summary

## Overview

The **Wage vs Essentials Analytics Module** is a comprehensive analytical tool that quantifies whether minimum wage increases keep up with essential-goods inflation. It provides evidence-driven insights for workers, policymakers, advocates, journalists, and educators through multi-dimensional affordability metrics.

## Product Thesis

This module addresses the critical question: "Has minimum wage growth kept pace with the rising cost of essential goods?" By converting both wage and price data into standardized metrics (particularly hours-of-work), the module enables users to understand purchasing power trends with scientific rigor and transparent methodology.

## Target Users & Top Jobs-to-Be-Done

### Primary Users
1. **Workers paid near minimum wage** - Need to understand their purchasing power changes
2. **Policymakers & advocates** - Require evidence for policy decisions and advocacy
3. **Journalists & educators** - Need citation-ready data and charts for reporting/teaching

### Core Jobs
1. See if minimum wage has maintained purchasing power
2. Identify which essentials outpaced wage growth
3. Generate shareable, defensible charts and methodology cards

## Key Features Implemented

### 1. Affordability Dashboard (`AffordabilityDashboard.tsx`)

**Purpose**: Primary view showing whether wages "kept up" or "lagged" behind essential goods inflation

**Key Components**:
- **Verdict Card**: Clear "kept up" / "lagged" / "unclear" determination with confidence badge
- **Affordability Ratio**: basket_hours(t2) / basket_hours(t1) - the primary metric
  - Ratio > 1.00 = Worsened (requires MORE work hours)
  - Ratio = 1.00 = No change
  - Ratio < 1.00 = Improved (requires FEWER work hours)
- **Indexed Trend Chart**: Wage vs Basket cost both normalized to 100 at base date
- **Growth Comparison**: Side-by-side wage growth vs price growth
- **Relative Outpacing**: Shows if prices grew faster than wages

**Formulas Used**:
```
affordability_ratio = basket_hours(t2) / basket_hours(t1)
basket_hours(t) = basket_cost(t) / wage(t)
relative_outpacing = basket_growth - wage_growth
```

### 2. Item Outpacing Rankings (`OutpacingRankings.tsx`)

**Purpose**: Detailed table showing which specific items' prices grew faster than wages

**Key Components**:
- **Ranked Table**: All basket items sorted by relative outpacing
- **Visualization Bars**: Visual representation of outpacing magnitude
- **Top/Bottom Lists**: Most and least outpacing items highlighted
- **Multi-Metric Display**: Shows price growth, wage growth, and affordability change

**Formula**:
```
relative_outpacing_i = item_growth_i - wage_growth
where:
  item_growth_i = (price_t2 - price_t1) / price_t1
  wage_growth = (wage_t2 - wage_t1) / wage_t1
```

### 3. Wage Increase Event Studies (`EventStudyView.tsx`)

**Purpose**: Analyzes affordability changes around specific minimum wage increase dates

**Key Components**:
- **Event Detection**: Automatically identifies wage increase effective dates
- **Pre/Post Windows**: Configurable 3/6/12 month analysis windows
- **Basket Impact**: Shows total hours-of-work change after wage increase
- **Item-Level Breakdown**: Individual item affordability changes
- **Sensitivity Analysis**: Multiple window lengths available

**Methodology**:
- Detects wage changes >1% as events
- Compares basket_hours in window before vs after effective date
- Shows Δhours = hours_post - hours_pre

### 4. Analytics Methodology (`AnalyticsMethodology.tsx`)

**Purpose**: Complete transparency on calculations, sources, and limitations

**Key Components**:
- **Core Definitions**: Mathematical notation for all variables
- **Formulas Section**: Every calculation explained with examples
- **Verdict Logic**: Transparent thresholds and confidence rules
- **Data Sources**: Complete provenance with timestamps
- **CPI Information**: Base year, latest values, series length
- **Limitations**: Explicit caveats about data quality and scope
- **Exportable Methodology Card**: Full documentation download

### 5. Indexed Trend Chart (`IndexedTrendChart.tsx`)

**Purpose**: D3-powered visualization comparing wage and basket indices

**Features**:
- Both series normalized to 100 at user-selected base date
- Smooth curves with proper axes and legends
- Reference line at 100 baseline
- Responsive design with proper margins

## Core Calculations & Formulas

### Hours of Work (Primary Affordability Metric)

```
For single item:
  hours_i(t) = p_i(t) / w(t)

For basket:
  basket_cost(t) = Σ_i p_i(t) × q_i
  basket_hours(t) = basket_cost(t) / w(t)
```

### Growth Rates

```
Wage growth:
  wage_growth(t1,t2) = [w(t2) / w(t1)] - 1

Item price growth:
  item_growth_i(t1,t2) = [p_i(t2) / p_i(t1)] - 1

Basket growth:
  basket_growth(t1,t2) = [basket_cost(t2) / basket_cost(t1)] - 1
```

### Real-Dollar Adjustments (CPI-based)

```
Real wage:
  real_wage(t) = w(t) / I(t)

Real price:
  real_price_i(t) = p_i(t) / I(t)

where I(t) = CPI at time t (base year 1982-84 = 100)
```

### Affordability Change Test

```
affordability_ratio = hours(t2) / hours(t1)

Interpretation:
  > 1.00: Requires MORE work hours (worse)
  = 1.00: No change
  < 1.00: Requires FEWER work hours (better)
```

### Relative Outpacing

```
For item:
  relative_outpacing_i = item_growth_i - wage_growth

For basket:
  outpacing_basket = basket_growth - wage_growth

Interpretation:
  Positive: Prices outpaced wages (worsened)
  Negative: Wages outpaced prices (improved)
```

### Indexed Series (Comparability View)

```
Wage index:
  wage_index(t) = 100 × [w(t) / w(t0)]

Basket index:
  basket_index(t) = 100 × [basket_cost(t) / basket_cost(t0)]

where t0 = base date (user-selectable)
```

## Verdict Logic

### Default Rules (Configurable)

```
"Kept Up": basket_affordability_ratio ≤ 1.00
"Lagged": basket_affordability_ratio > 1.00
"Unclear": Data coverage < 70%
```

### Confidence Levels

Based on data coverage (% of basket items with complete data):
- **High**: ≥90% coverage
- **Medium**: 70-89% coverage
- **Low**: <70% coverage (verdict = "unclear")

## Data Sources Integration

### Minimum Wage Data
- **Source**: Bureau of Labor Statistics (BLS)
- **Attributes**: Effective dates, jurisdiction (federal/state/city), stepwise changes
- **Handling**: Carry-forward last effective wage until next change

### Price Data
- **Sources**: USDA Agricultural Marketing Service, EIA Energy Data
- **Coverage**: 8 essential items (eggs, milk, butter, cheese, beef, gas, propane)
- **Frequency**: Monthly observations

### CPI Data (New Integration)
- **Source**: BLS Consumer Price Index
- **Base Year**: 1982-84 = 100
- **Use**: Inflation adjustment for "real dollars" calculations
- **Formula**: `real_price = nominal_price / (CPI / 100)`

## Configuration Options

Users can customize:
- **Region**: US-National (extensible to states/cities)
- **Wage Type**: Minimum wage or Median wage
- **Time Window**: 1Y, 3Y, 5Y, 10Y, or All
- **Base Date**: Reference point for indexed series
- **Metric Mode**: Nominal $, Real $ (CPI-adj), or Hours-of-Work
- **Verdict Threshold**: Affordability ratio cutoff (default 1.00)
- **Event Window**: 3, 6, or 12 month pre/post periods

## Export & Sharing

### Methodology Card Export
Complete document including:
- All formulas with LaTeX-style notation
- Data source URLs and timestamps
- Region and jurisdiction details
- Base dates and time windows
- Basket composition
- CPI series information
- Confidence flags and coverage metrics
- Limitations and caveats
- Reproducibility instructions

### Format
Plain text (.txt) with clear sections and ASCII formatting for universal compatibility

## Technical Implementation

### File Structure
```
src/
├── components/
│   ├── AnalyticsView.tsx           # Main analytics container
│   ├── AffordabilityDashboard.tsx  # Verdict & primary metrics
│   ├── OutpacingRankings.tsx       # Item ranking table
│   ├── EventStudyView.tsx          # Wage increase analysis
│   ├── AnalyticsMethodology.tsx    # Documentation & export
│   └── IndexedTrendChart.tsx       # D3 visualization
├── lib/
│   ├── types.ts                    # Analytics types
│   └── data.ts                     # Calculation functions
```

### Key Functions Added to `data.ts`

1. **`detectWageIncreaseEvents()`**: Finds wage hike dates
2. **`calculateAffordabilityMetrics()`**: Per-item analysis
3. **`calculateBasketAffordabilityMetrics()`**: Basket-level verdict
4. **`calculateIndexedSeries()`**: Normalize to base=100
5. **`getCPIHistory()`**: Retrieve CPI time series
6. **`getCPIForDate()`**: Get CPI for specific date
7. **`calculateRealPrice()`**: Inflation-adjust prices

### New Types

```typescript
interface WageIncreaseEvent {
  effectiveDate: string
  oldWage: number
  newWage: number
  increase: number
  increasePercent: number
  region: string
  jurisdiction: 'federal' | 'state' | 'city'
}

interface AffordabilityMetrics {
  itemId: string
  itemName: string
  hoursT1: number
  hoursT2: number
  affordabilityRatio: number
  absoluteChange: number
  percentChange: number
  nominalGrowth: number
  wageGrowth: number
  relativeOutpacing: number
}

interface BasketAffordabilityMetrics {
  basketCostT1: number
  basketCostT2: number
  hoursT1: number
  hoursT2: number
  affordabilityRatio: number
  absoluteChange: number
  percentChange: number
  nominalGrowth: number
  wageGrowth: number
  relativeOutpacing: number
  verdict: 'kept-up' | 'lagged' | 'unclear'
  confidenceLevel: 'high' | 'medium' | 'low'
}

interface AnalyticsConfig {
  region: string
  dateRange: { start: string; end: string }
  baseDate: string
  wageType: 'minimum' | 'median'
  basketItemIds: string[]
  metricMode: MetricMode
  verdictThreshold: number
  eventWindowMonths: number
}
```

## Not Included (By Design)

The following are **explicitly excluded** per MVP scope:
- ❌ Partisan messaging or blame assignment
- ❌ Forecasting or predictive analytics
- ❌ Individualized financial advice
- ❌ Political campaigning content
- ❌ Advocacy statements (neutral presentation only)

## Nonfunctional Requirements Met

✅ **Deterministic**: All calculations reproducible with same inputs
✅ **Traceable**: Every metric traces back to raw data and formula
✅ **Transparent**: Complete methodology disclosure
✅ **Performant**: Charts render quickly for 10+ year windows
✅ **Offline-ready**: Calculations run client-side (cached views work offline)
✅ **Audit-ready**: Methodology cards include all provenance data

## Future Extensibility

The module is designed for future enhancements:
- **Additional wage types**: Sector-specific wages, living wages
- **Regional expansion**: State and city-level minimum wages
- **More items**: Rent, utilities, healthcare costs
- **Distributional analysis**: Percentile breakdowns where data supports
- **Crowdsourced prices**: Behind feature flag with moderation
- **Multi-jurisdiction comparison**: Compare federal vs state vs local

## Usage Flow

1. **User navigates to Analytics tab** from main navigation
2. **Configure analysis**: Select region, wage type, time window
3. **View Dashboard**: See verdict, affordability ratio, indexed trends
4. **Explore Rankings**: Identify which items outpaced wages most
5. **Analyze Events**: Study affordability around wage increase dates
6. **Review Methodology**: Understand formulas and limitations
7. **Export Card**: Download complete methodology with data sources

## Validation & Testing

Key validation points:
- Affordability ratios calculated correctly (manual spot checks)
- Event detection finds wage increases accurately
- Indexed series normalize to 100 at base date
- CPI adjustments use correct base year
- Confidence levels reflect actual data coverage
- Exports contain complete information

## Documentation

All formulas and methodology are documented in:
1. **In-app**: AnalyticsMethodology component with interactive tooltips
2. **Exportable**: Methodology card with complete specifications
3. **PRD**: Updated with analytics module feature descriptions
4. **Code comments**: Calculation functions annotated

## Summary

The Wage vs Essentials Analytics Module provides a rigorous, transparent, and accessible way to analyze whether minimum wage increases have kept pace with essential goods inflation. By focusing on the "hours of work" metric and providing multi-dimensional analysis (dashboard, rankings, event studies), it serves the needs of workers, policymakers, journalists, and educators who require defensible evidence for understanding purchasing power trends.

The implementation prioritizes:
- **Transparency**: All formulas exposed
- **Rigor**: Academically sound methodology
- **Accessibility**: Clear visualizations and plain language
- **Reproducibility**: Complete documentation and data provenance
- **Neutrality**: No partisan messaging, just evidence

This makes it a trustworthy tool for evidence-based discussions about wage policy and affordability.
