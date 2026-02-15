# Chronos: Adding New Items to the Expanded Catalog

## Quick Start Guide for Developers

### Adding a Single Item

1. **Open** `src/lib/expanded-catalog.ts`
2. **Add to** `EXPANDED_ITEMS` array:

```typescript
{
  id: 'item-name-unit',           // kebab-case, include unit
  name: 'Display Name',            // User-facing name
  category: 'produce',             // See categories below
  unitStandard: 'lb',              // Standard unit for this item
  acceptableAlternateUnits: ['oz', 'kg'],  // Other valid units
  conversions: UNIT_CONVERSIONS.filter(c => c.fromUnit === 'lb' || c.toUnit === 'lb'),
  description: 'Brief description of item variant (e.g., "Organic, fresh")',
  synonyms: ['alternate name 1', 'alternate name 2'],  // For search
  sourceSeriesIds: ['usda-nass'],  // Which sources provide this data
  regionCoverage: ['US-National'],  // Which regions have data
}
```

3. **Add base price** to `getBasePrice()` in `src/lib/data-connectors.ts`:

```typescript
const basePrices: Record<string, number> = {
  'item-name-unit': 5.00,  // Starting price for simulation
  // ...
}
```

4. **Test** by navigating to "Full Catalog" and searching for your item

### Available Categories

```typescript
'dairy'      // Milk, cheese, eggs, butter
'meat'       // Beef, pork (raw cuts)
'proteins'   // Chicken, fish, beans, legumes
'produce'    // Fresh fruits and vegetables
'grains'     // Rice, pasta, cereals
'staples'    // Flour, sugar, salt, bread, coffee
'household'  // Cleaning, paper products, diapers
'fuel'       // Gasoline, diesel, propane, heating oil
'utilities'  // Electricity, natural gas, water, rent
'inputs'     // Agricultural inputs (seeds, soil, fertilizer, feed)
```

### Standard Units

```typescript
// Weight
'lb'    // Pound
'oz'    // Ounce
'kg'    // Kilogram

// Volume
'gallon'  // US gallon
'liter'   // Liter

// Count
'dozen'   // 12 items
'count'   // Single item
'pack'    // Package/bundle
'roll'    // Roll (paper products)

// Energy
'kWh'     // Kilowatt-hour
'therm'   // Therm (natural gas)
'ccf'     // Hundred cubic feet

// Agriculture
'bushel'  // Bushel
```

### Adding Unit Conversions

If your item needs a new unit conversion, add it to `UNIT_CONVERSIONS`:

```typescript
export const UNIT_CONVERSIONS: UnitConversion[] = [
  // ...existing conversions
  { fromUnit: 'quart', toUnit: 'gallon', factor: 0.25 },
  { fromUnit: 'gallon', toUnit: 'quart', factor: 4 },
]
```

**Always add both directions** (A→B and B→A).

### Adding a New Data Source

1. **Add to** `EXPANDED_SOURCES` in `src/lib/expanded-catalog.ts`:

```typescript
{
  id: 'new-source-id',
  name: 'Official Source Name',
  provider: 'Organization Name',
  license: 'Public Domain' or 'Attribution Required',
  terms: 'Summary of usage terms',
  url: 'https://official-source.gov',
  retrievalTimestamp: new Date().toISOString(),
  isOfficial: true,  // Only true for government/primary sources
  reliabilityTier: 'tier-1',  // tier-1 = official, tier-2 = verified, tier-3 = community
  refreshSchedule: 'daily',   // 'manual' | 'hourly' | 'daily'
  coverageMap: {
    'US-National': ['item-id-1', 'item-id-2'],
  },
  seriesIdentifiers: ['API_SERIES_ID_1'],
  status: 'active',
}
```

2. **Add connector** to `DATA_CONNECTORS` in `src/lib/data-connectors.ts`:

```typescript
{
  id: 'new-source-connector',
  sourceId: 'new-source-id',
  name: 'Human-Readable Connector Name',
  enabled: true,
  featureFlag: 'connector-new-source',
  retryConfig: {
    maxRetries: 3,
    backoffMs: 1000,
    circuitBreakerThreshold: 5,
  },
  rateLimit: {
    requestsPerMinute: 60,
    requestsPerHour: 1000,
  },
  allowedDomains: ['official-source.gov', 'api.official-source.gov'],
}
```

3. **Update** `simulateFetch()` to handle your source (production: replace with real API calls)

### Adding a Basket Template

In `BASKET_TEMPLATES`:

```typescript
{
  id: 'template-id',
  name: 'Display Name',
  description: 'Brief description of household type',
  category: 'custom',  // 'family-4' | 'single-adult' | 'tradesperson' | 'custom'
  items: [
    { itemId: 'eggs-dozen', quantity: 2 },
    { itemId: 'milk-gallon', quantity: 1 },
    // ...more items
  ],
  isPublic: true,
}
```

### Testing Your Changes

1. **Start dev server**: `npm run dev`
2. **Navigate to**: "Full Catalog" tab
3. **Search** for your new item by name or synonym
4. **Verify**:
   - Item appears in correct category
   - Unit displays correctly
   - Synonyms work in search
   - Can add to comparison
   - Source shows in registry

### Common Pitfalls

❌ **Forgetting both conversion directions**
```typescript
// WRONG
{ fromUnit: 'lb', toUnit: 'oz', factor: 16 }

// CORRECT
{ fromUnit: 'lb', toUnit: 'oz', factor: 16 },
{ fromUnit: 'oz', toUnit: 'lb', factor: 0.0625 },
```

❌ **Using undefined category**
```typescript
category: 'groceries'  // Not in the enum!
```

❌ **Forgetting sourceSeriesIds**
```typescript
sourceSeriesIds: [],  // Item won't connect to any data source!
```

❌ **Using 'count' for unit when 'dozen' is more appropriate**
```typescript
// For eggs, use:
unitStandard: 'dozen'  // NOT 'count'
```

### Validation Checklist

Before committing:
- [ ] Item ID follows pattern: `{name}-{unit}` in kebab-case
- [ ] Category is valid (from enum)
- [ ] Unit conversions include both directions
- [ ] Synonyms help users find the item
- [ ] Base price added to `getBasePrice()`
- [ ] sourceSeriesIds references existing source
- [ ] regionCoverage is realistic
- [ ] Item appears in Full Catalog
- [ ] Search finds item by synonym
- [ ] Unit displays correctly

### Production Considerations

When deploying to production:

1. **Replace `simulateFetch()`** with real API calls:
   ```typescript
   const response = await fetch(`https://api.source.gov/series/${itemId}`)
   ```

2. **Store API keys server-side**:
   - Use environment variables
   - Never commit keys to repo
   - Use signed requests if possible

3. **Implement caching**:
   - Cache API responses
   - Serve stale data if API down
   - Background refresh

4. **Add monitoring**:
   - Log connector failures
   - Alert on circuit breaker trips
   - Track confidence score trends

### Need Help?

- **Data Quality Issues**: Check `ValidationResult` in console
- **Unit Conversion Errors**: Verify both directions defined
- **Source Not Showing**: Check `sourceSeriesIds` matches `EXPANDED_SOURCES[].id`
- **Search Not Finding Item**: Add more synonyms

### Example: Complete Item Addition

```typescript
// 1. Add to EXPANDED_ITEMS
{
  id: 'orange-juice-gallon',
  name: 'Orange Juice',
  category: 'dairy',  // Refrigerated section
  unitStandard: 'gallon',
  acceptableAlternateUnits: ['liter'],
  conversions: [
    { fromUnit: 'liter', toUnit: 'gallon', factor: 0.264172 }
  ],
  description: '100% orange juice, not from concentrate',
  synonyms: ['OJ', 'juice', 'citrus juice'],
  sourceSeriesIds: ['usda-ams'],
  regionCoverage: ['US-National'],
}

// 2. Add base price
const basePrices: Record<string, number> = {
  'orange-juice-gallon': 4.50,
  // ...
}

// Done! Item now searchable and trackable
```
