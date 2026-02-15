# Loading States Documentation

## Overview

The Chronos application includes a comprehensive set of animated loading states built with the application's logo. These loading indicators maintain brand consistency while providing clear feedback during asynchronous operations.

## Components

### Logo Variants

#### 1. Static Logo
```tsx
import { Logo } from '@/components/Logo'

<Logo size={40} className="text-primary" />
```
The standard, non-animated logo for static display in headers and branding contexts.

#### 2. Animated Logo
```tsx
<Logo animated size={64} className="text-primary" />
```
Features a smooth draw-in animation where paths animate sequentially. Best used for:
- Initial page loads
- App launch screens
- Modal openings

**Animation Details:**
- Duration: ~1 second
- Effect: Sequential path drawing with staggered timing
- Plays once on mount

#### 3. Logo Spinner
```tsx
import { LogoSpinner } from '@/components/Logo'

<LogoSpinner size={40} className="text-primary" />
```
A rotating circular spinner based on the logo aesthetic. Best used for:
- Async data fetching
- API calls in progress
- General loading operations

**Animation Details:**
- Duration: 2 seconds per rotation
- Effect: Continuous circular rotation with animated stroke dash
- Loops infinitely

#### 4. Logo Pulse
```tsx
import { LogoPulse } from '@/components/Logo'

<LogoPulse size={48} className="text-primary" />
```
A pulsing animation with scale and opacity changes. Best used for:
- Data refresh operations
- Real-time updates
- Background sync indicators

**Animation Details:**
- Duration: 1.5 seconds per pulse
- Effect: Scale expansion (1.0 → 1.15) with opacity fade, plus chevron motion
- Loops infinitely

## Pre-built Loading Components

### FullPageLoader
```tsx
import { FullPageLoader } from '@/components/LoadingStates'

<FullPageLoader />
```
Covers the entire viewport with a semi-transparent backdrop and centered animated logo.

**Use Cases:**
- Initial app load
- Major route transitions
- Full-page data refresh

### InlineLoader
```tsx
import { InlineLoader } from '@/components/LoadingStates'

<InlineLoader text="Loading chart data..." size={40} />
```
Displays a spinner with optional text for inline loading states within content sections.

**Props:**
- `size?: number` - Logo size (default: 40)
- `text?: string` - Optional loading message

### CardLoader
```tsx
import { CardLoader } from '@/components/LoadingStates'

<CardLoader text="Fetching analytics..." />
```
Optimized for loading states within Card components, includes padding and vertical centering.

**Props:**
- `text?: string` - Optional loading message

### CompactLoader
```tsx
import { CompactLoader } from '@/components/LoadingStates'

<CompactLoader size={24} />
```
Minimal spinner for buttons and tight spaces.

**Props:**
- `size?: number` - Logo size (default: 24)

### DataRefreshLoader
```tsx
import { DataRefreshLoader } from '@/components/LoadingStates'

<DataRefreshLoader />
```
Specialized loader for data refresh operations, uses accent color to distinguish from primary loading states.

## Usage Guidelines

### Choosing the Right Loader

| Scenario | Recommended Component | Reason |
|----------|----------------------|---------|
| Initial app load | `FullPageLoader` | Covers entire screen during bootstrap |
| Route change | `<Logo animated />` | Quick, branded transition |
| Chart loading | `InlineLoader` | Non-blocking, contextual feedback |
| Card content loading | `CardLoader` | Properly padded for card layouts |
| Button loading state | `CompactLoader` | Small enough for button contexts |
| Data refresh | `DataRefreshLoader` | Distinct color signals update |
| Modal/dialog loading | `<Logo animated />` | Elegant branded experience |

### Size Recommendations

- **Extra Small (16-20px):** Button loading states, inline icons
- **Small (24-32px):** Compact loaders, tight UI spaces
- **Medium (40-48px):** Standard loading indicators, inline content
- **Large (64-80px):** Prominent loading states, full-page loaders
- **Extra Large (96px+):** App launch screens, splash screens

### Animation Performance

All animations use:
- **Framer Motion** for declarative animations
- **GPU-accelerated transforms** (scale, rotate, opacity)
- **Will-change optimization** automatically applied
- **Reduced motion support** respects user preferences

### Accessibility

Loading states include:
- Semantic HTML structure
- ARIA live regions for screen readers (when using text)
- Color-independent indicators (motion-based)
- Reduced motion media query support

### Color Customization

Use Tailwind utility classes to customize colors:

```tsx
<LogoSpinner className="text-accent" />     // Accent color
<LogoSpinner className="text-primary" />    // Primary color (default)
<LogoSpinner className="text-destructive" /> // Error state
<LogoPulse className="text-secondary" />     // Secondary color
```

## Examples

### Loading Data in a Component

```tsx
import { useState, useEffect } from 'react'
import { InlineLoader } from '@/components/LoadingStates'

export function DataView() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    fetchData().then(result => {
      setData(result)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return <InlineLoader text="Loading data..." />
  }

  return <div>{/* Render data */}</div>
}
```

### Button with Loading State

```tsx
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { CompactLoader } from '@/components/LoadingStates'

export function SubmitButton() {
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    await submitData()
    setLoading(false)
  }

  return (
    <Button onClick={handleSubmit} disabled={loading}>
      {loading ? (
        <span className="flex items-center gap-2">
          <CompactLoader size={16} />
          Processing...
        </span>
      ) : (
        'Submit'
      )}
    </Button>
  )
}
```

### Card with Loading State

```tsx
import { Card } from '@/components/ui/card'
import { CardLoader } from '@/components/LoadingStates'

export function AnalyticsCard({ loading, data }) {
  return (
    <Card>
      {loading ? (
        <CardLoader text="Computing analytics..." />
      ) : (
        <div className="p-6">{/* Render data */}</div>
      )}
    </Card>
  )
}
```

### Conditional Full Page Loading

```tsx
import { FullPageLoader } from '@/components/LoadingStates'

export function App() {
  const [initializing, setInitializing] = useState(true)

  useEffect(() => {
    initialize().then(() => setInitializing(false))
  }, [])

  if (initializing) {
    return <FullPageLoader />
  }

  return <MainApp />
}
```

## Testing the Loading States

Visit `#loading` in the application to see an interactive showcase of all loading states with:
- Live examples of each variant
- Size comparisons
- Interactive demos
- Implementation code snippets

## Technical Details

### Dependencies
- `framer-motion@^12.23.25` - Animation library
- React 19 - Component framework

### File Locations
- Logo components: `/src/components/Logo.tsx`
- Loading state components: `/src/components/LoadingStates.tsx`
- Interactive examples: `/src/components/LoadingStateExample.tsx`

### Animation Specifications

**Animated Logo:**
- Left path: 0.8s draw-in, ease-out
- Right path: 0.8s draw-in, 0.1s delay, ease-out
- Center circle: 0.4s scale-in, 0.6s delay, spring physics
- Bottom line: 0.5s draw-in, 0.4s delay, ease-out
- Side chevrons: 0.4s slide-in, 0.8s delay, ease-out

**Logo Spinner:**
- Rotation: 360° every 2s, linear
- Stroke dash: Animated offset, 1.5s loop, linear
- Circle radius: 40 (relative to 100x100 viewBox)

**Logo Pulse:**
- Background circle: 1.5s scale (1.0 → 1.15 → 1.0), ease-in-out
- Center circle: 1.5s scale (1.0 → 1.3 → 1.0), ease-in-out
- Chevrons: 1.5s horizontal motion (±2px), ease-in-out
- All animations synchronized, infinite loop

## Future Enhancements

Potential additions:
- Progress bar variant with percentage display
- Skeleton loader with logo integration
- Success/error state animations
- Customizable animation speeds
- Additional color scheme presets
