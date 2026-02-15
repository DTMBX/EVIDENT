# Chronos Brand Guidelines v2.0
## Dark-Truth Brand System

---

## Brand Thesis

**"Fiat is a dead-end"** — documented with forensic precision, without partisan blame.

Chronos reveals the slow decay of purchasing power through transparent data visualization. Our brand communicates **data truth** through:

- **Dark-theme-first**: High contrast, accessibility-respectful
- **Forensic Ledger**: Precise as a modern audit trail
- **Gothic Gravitas**: Sober without melodrama
- **Extreme Legibility**: Readable at all scales
- **Non-partisan**: Evidence over ideology

The visual identity evokes a **modern forensic ledger meets archival monument**—where each data point is etched into history, and declining purchasing power is documented with the solemnity it deserves.

---

## Overview

**Chronos** is a generational economic insights platform that helps Americans of all ages explore long-term price trends, wage growth, and volatility through transparent data visualization. The name "Chronos" evokes time, continuity, and the passage of economic history across generations.

## Brand Identity

### Name
**Chronos** - From the Greek god of time, representing:
- **Generational continuity** - Tracking economic experiences across decades
- **Historical perspective** - Long-term timeline analysis (1950-present)
- **Temporal measurement** - "Hours of work" affordability metrics
- **Transparency** - Clear, time-stamped data provenance

### Tagline
**Generational Economic Insights**

### Brand Promise
Building shared understanding across generations through transparent data exploration rather than blame or division.

---

## Logo

### Primary Mark: The Marker

The Chronos logo is an abstract **headstone/marker emblem** that simultaneously reads as:

1. **Monument/Gravestone** — Marking purchasing power's declining trajectory
2. **Ledger Page** — Grid structure for precise accounting
3. **Chart** — Rising/falling sparkline embedded in the form
4. **Timestamp** — Small "mint mark" circle as authentication seal

The design features:
- **Tombstone silhouette** with rounded top (gravestone architecture)
- **Ledger grid** (horizontal and vertical lines creating accounting structure)
- **Sparkline** (declining trend line across the center)
- **Mint mark seal** (concentric circles in lower right, like a certification stamp)
- **Baseline** (strong horizontal foundation representing timeline)

### Logo Variants

1. **Primary Logo** — Full mark with all elements
2. **LogoIcon Square** — Icon-only, optimized for app icons
3. **LogoIcon Circle** — Icon with circular frame for avatars/badges
4. **LogoLockup** — Icon + "CHRONOS" wordmark (horizontal)
5. **Monochrome** — Single color, no opacity variations
6. **Inverted** — Light mode version (same structure, inverted contrast)

### Logo Usage

```tsx
import { Logo, LogoIcon, LogoLockup } from '@/components/Logo'

// Default usage (dark theme optimized)
<Logo size={40} className="text-primary" />

// Animated splash variant
<Logo size={64} animated={true} className="text-primary" />

// Icon-only square
<LogoIcon size={32} variant="square" className="text-foreground" />

// Icon-only circle (for avatars)
<LogoIcon size={48} variant="circle" className="text-primary" />

// Full lockup with wordmark
<LogoLockup height={48} className="text-foreground" />
```

**Minimum Sizes:**
- Lockup: 120px width minimum
- Icon-only: 24px minimum (32px recommended)
- Favicon: 16px (simplified variant automatically used in favicons)

**Clear Space:** Maintain padding equal to 25% of logo height on all sides

**Color Usage:**
- **Primary**: Use `text-primary` or `text-accent` on dark backgrounds
- **Monochrome Dark**: Use `text-foreground` for neutral dark theme
- **Monochrome Light**: Use white or `text-background` on light surfaces
- **Never**: Use on mid-tone backgrounds without sufficient contrast (4.5:1 minimum)

### Animated Logo Variants

**Splash Animation** (plays once on load, 2 seconds):
```tsx
<Logo size={64} animated={true} className="text-primary" />
```

Sequence:
1. Grid fades in (0–300ms)
2. Headstone outline draws (300–1100ms)
3. Sparkline draws left-to-right (700–1600ms)
4. Mint mark seal pulses (1400–1800ms)
5. Baseline appears (1100–1600ms)
6. Hold final state

**Loading State** (infinite loop):
```tsx
import { LogoSpinner, LogoPulse } from '@/components/Logo'

<LogoSpinner size={40} className="text-primary" />
<LogoPulse size={40} className="text-accent" />
```

- **LogoSpinner**: Sparkline oscillates vertically (±2px), seal pulses opacity
- **LogoPulse**: Entire mark pulses scale and opacity subtly

**Reduced Motion**: All animations honor `prefers-reduced-motion` and fall back to static fade-in (400ms).

---

## Icon System

### Design Principles

1. **24×24px Grid** — All icons built on consistent base grid
2. **2px Stroke Weight** — Regular weight (1.5px thin, 2.5px bold variants)
3. **Rounded Joins** — 2px corner radius, rounded caps for approachability
4. **Forensic Aesthetic** — Grid patterns, ledger lines, archival stamps
5. **Optical Balance** — Visual weight adjusted for perceived consistency
6. **High Legibility** — Clear rendering from 20px to 64px

### Brand-Specific Icons

**Forensic/Archival Set** (unique to Chronos):
- **Headstone** — Monument marker with sparkline and seal
- **Ledger** — Grid accounting book with mint mark
- **MintMark** — Concentric circle authentication seal
- **ArchivalStamp** — Verification stamp with checkmark
- **DecayLine** — Descending trend line (purchasing power)
- **Flatline** — Horizontal baseline with milestone dots
- **GridPattern** — Ledger accounting grid
- **EngravedLine** — Fine parallel lines (currency aesthetic)
- **Forensic** — Magnifying glass over ledger lines
- **Truth** — Shield with verification check and ledger lines
- **Evidence** — Document with magnifying glass
- **HourglassDecay** — Hourglass with sand accumulation (time decay)
- **ArchiveBox** — Storage box with seal

**Usage:**
```tsx
import { 
  HeadstoneIcon, 
  LedgerIcon, 
  MintMarkIcon,
  ForensicIcon 
} from '@/components/brand-icons'

<HeadstoneIcon size={24} weight="regular" className="text-foreground" />
<MintMarkIcon size={20} className="text-accent" />
<ForensicIcon size={32} weight="bold" className="text-primary" />
```

### Core Feature Icons

**Navigation Icons**:
- **Home** — Dashboard with door entry
- **Explore** — Magnifying glass with plus
- **Compare** — Side-by-side bars
- **Analytics** — Line chart with data points
- **Settings** — Gear with adjustment indicators

**Feature Icons**:
- **Timeline** — Horizontal arrow with milestone dots
- **Generations** — Overlapping figures representing cohorts
- **Affordability** — Clock face with directional arrows (hours of work)
- **Volatility** — Fluctuating line with stability bands
- **Basket** — Shopping basket with essential goods
- **Insight** — Lightbulb with information
- **Education** — Graduation cap with pages
- **Dialogue** — Speech bubble with text

**Data & Source Icons**:
- **DataSource** — Database stack with refresh
- **Methodology** — Document with formula notation
- **Refresh** — Circular arrow
- **Verified** — Shield with checkmark
- **Warning** — Alert triangle

**Action Icons**:
- **Share** — Connected nodes (permalink)
- **Export** — Upward arrow from box
- **Filter** — Sliders with adjustment
- **Calendar** — Date grid

**Indicator Icons**:
- **TrendUp** — Rising arrow (price increase)
- **TrendDown** — Falling arrow (price decrease)
- **Clock** — Time measurement (hours of work)

### Icon Weight Variants

```tsx
// Regular weight (default)
<AnalyticsIcon size={24} weight="regular" />

// Bold weight (active state, emphasis)
<AnalyticsIcon size={24} weight="bold" className="text-primary" />

// Thin weight (muted state, secondary)
<AnalyticsIcon size={24} weight="thin" className="text-muted-foreground" />
```

### Semantic Color Usage

```tsx
// Success/increase (neutral green, not celebratory)
<TrendUpIcon size={18} className="text-increase" />

// Warning/decrease (amber-orange, neutral)
<TrendDownIcon size={18} className="text-decrease" />

// Verification/trust
<VerifiedIcon size={18} className="text-accent" />

// Alerts/errors
<WarningIcon size={18} className="text-destructive" />

// Brand accent (highlights, active)
<MintMarkIcon size={16} className="text-accent" />
```

---

## Color System: Dark-Theme-First

### Philosophy

Chronos uses a **dark-first color system** designed for:
- **High contrast** without neon glare
- **Forensic clarity** (readable data on dark surfaces)
- **Gothic gravitas** (sober, serious, trustworthy)
- **Accessibility** (WCAG AA minimum, AAA where possible)
- **Light mode** as secondary "paper ledger" aesthetic

### Dark Theme (Default)

**Neutrals** (backgrounds and surfaces):
```css
--background: oklch(0.12 0.01 250);          /* Deep slate, almost black */
--foreground: oklch(0.95 0.01 250);          /* High-contrast body text */

--surface: oklch(0.16 0.01 250);             /* Elevated panels */
--surface-elevated: oklch(0.20 0.01 250);    /* Modal overlays, dropdowns */

--border: oklch(0.28 0.01 250);              /* Subtle dividers */
--border-strong: oklch(0.35 0.01 250);       /* Emphasized borders */

--text-secondary: oklch(0.75 0.01 250);      /* Metadata, labels */
--text-muted: oklch(0.55 0.01 250);          /* Disabled, placeholders */
```

**Brand Colors**:
```css
--primary: oklch(0.70 0.18 200);             /* Cold steel blue */
--primary-foreground: oklch(0.12 0.01 250);  /* Dark text on primary */

--accent: oklch(0.72 0.15 140);              /* Forensic teal */
--accent-foreground: oklch(0.12 0.01 250);   /* Dark text on accent */
```

**Semantic Colors**:
```css
--success: oklch(0.65 0.15 145);             /* Neutral green (not celebratory) */
--warning: oklch(0.68 0.18 60);              /* Amber, informational */
--danger: oklch(0.60 0.20 25);               /* Warm red, errors */
--info: oklch(0.70 0.15 230);                /* Cool blue, hints */

--increase: oklch(0.65 0.15 145);            /* Price/wage increases */
--decrease: oklch(0.60 0.20 25);             /* Price/wage decreases */
```

**Chart Colors** (colorblind-safe with distinct line styles):
```css
--chart-1: oklch(0.68 0.20 200);   /* Steel blue + solid line */
--chart-2: oklch(0.72 0.18 30);    /* Amber + dashed line */
--chart-3: oklch(0.66 0.16 145);   /* Teal + dotted line */
--chart-4: oklch(0.64 0.17 300);   /* Purple + dash-dot line */
--chart-5: oklch(0.70 0.14 170);   /* Seafoam + long-dash line */

--chart-axis: oklch(0.40 0.01 250);           /* Axis lines */
--chart-grid: oklch(0.22 0.01 250);           /* Gridlines, subtle */
```

### Light Theme ("Paper Ledger")

**Neutrals**:
```css
.light {
  --background: oklch(0.98 0.005 250);        /* Warm paper white */
  --foreground: oklch(0.18 0.01 250);         /* Dark ink */
  
  --surface: oklch(0.95 0.005 250);           /* Card containers */
  --surface-elevated: oklch(0.99 0.005 250);  /* Elevated modals */
  
  --border: oklch(0.85 0.01 250);             /* Visible dividers */
  --border-strong: oklch(0.70 0.01 250);      /* Emphasized borders */
  
  --text-secondary: oklch(0.40 0.01 250);     /* Metadata */
  --text-muted: oklch(0.58 0.01 250);         /* Muted text */
}
```

**Brand Colors** (adjusted for light backgrounds):
```css
.light {
  --primary: oklch(0.45 0.18 200);            /* Darker blue for contrast */
  --primary-foreground: oklch(0.98 0.005 250);

  --accent: oklch(0.50 0.15 140);             /* Darker teal */
  --accent-foreground: oklch(0.98 0.005 250);
}
```

**Auto-Switch & Manual Override**:
```tsx
// Auto-switch based on system preference
@media (prefers-color-scheme: light) {
  :root:not(.dark) {
    /* Light theme tokens applied */
  }
}

// Manual override in HTML
<html class="dark">  <!-- Forces dark theme -->
<html class="light"> <!-- Forces light theme -->
```

### Accessibility Standards

**All pairings meet WCAG AA minimum (4.5:1 for text, 3:1 for UI components):**

**Dark Theme Contrasts:**
- Background → Foreground: **16.8:1** ✓ (AAA)
- Surface → Foreground: **14.2:1** ✓ (AAA)
- Primary → Background: **5.8:1** ✓ (AA)
- Accent → Background: **6.2:1** ✓ (AA)
- Text-secondary → Background: **7.5:1** ✓ (AA)

**Light Theme Contrasts:**
- Background → Foreground: **15.4:1** ✓ (AAA)
- Primary → Background: **9.1:1** ✓ (AAA)
- Accent → Background: **7.8:1** ✓ (AA)

**Colorblind Considerations:**
- Chart lines MUST use distinct dash patterns (solid, dashed, dotted, dash-dot, long-dash) in addition to color
- Success/warning/danger MUST pair with icons, never color alone
- Never use color as the sole indicator of meaning

### Usage Examples

```tsx
// Backgrounds
<div className="bg-background text-foreground">
<div className="bg-surface border border-border">
<div className="bg-surface-elevated shadow-lg">

// Brand colors
<Button className="bg-primary text-primary-foreground">
<Badge className="bg-accent text-accent-foreground">

// Semantic colors
<span className="text-increase">+5.2%</span>
<span className="text-decrease">-2.1%</span>
<Alert className="border-warning text-warning">

// Chart colors
<path stroke="var(--chart-1)" strokeDasharray="4 0" />
<path stroke="var(--chart-2)" strokeDasharray="8 4" />

// Text hierarchy
<p className="text-foreground">Primary text</p>
<span className="text-text-secondary">Metadata</span>
<label className="text-text-muted">Disabled</label>
```

---

## Typography

### Font Selection

**Display & Headings: JetBrains Mono** Bold/SemiBold
- Monospaced precision with slightly gothic character
- Distinctive but trustworthy
- Excellent rendering at large sizes
- Creates "forensic ledger" aesthetic
- Use for: H1, H2, logo wordmark, large metrics, emphasis

**Body & UI: Inter** Regular/Medium
- Modern, highly legible sans-serif
- Optimized for screens and small sizes
- Timeless, avoids trendiness
- Exceptional readability in paragraphs
- Use for: Body text, UI labels, tables, buttons, navigation

**Data & Code: JetBrains Mono** Regular/Medium
- Tabular figures for data alignment
- Clear distinction of characters (0 vs O, 1 vs l)
- Monospaced for column alignment
- Use for: Formulas, source citations, timestamps, code blocks, numeric displays

### Type Scale

```css
/* Font Sizes */
--font-size-xs: 0.75rem;      /* 12px - Tiny labels, footnotes */
--font-size-sm: 0.875rem;     /* 14px - Metadata, small UI */
--font-size-base: 1rem;       /* 16px - Body text */
--font-size-lg: 1.125rem;     /* 18px - Emphasized body */
--font-size-xl: 1.25rem;      /* 20px - H3 */
--font-size-2xl: 1.5rem;      /* 24px - H2 */
--font-size-3xl: 2rem;        /* 32px - H1 */
--font-size-4xl: 2.5rem;      /* 40px - Hero headings */
--font-size-metric: 3rem;     /* 48px - Dashboard metrics */

/* Weights */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* Letter Spacing */
--letter-spacing-tight: -0.02em;   /* Large headings */
--letter-spacing-normal: 0;
--letter-spacing-wide: 0.02em;     /* Small caps, labels */
--letter-spacing-mono: 0.01em;     /* Monospace data */

/* Line Heights */
--line-height-tight: 1.1;      /* H1, large metrics */
--line-height-snug: 1.3;       /* H2, H3 */
--line-height-normal: 1.5;     /* Body text */
--line-height-relaxed: 1.7;    /* Long-form content */
```

### Typographic Hierarchy

**H1 (Page Titles, Dashboard Headlines):**
```css
font-family: 'JetBrains Mono', monospace;
font-size: 2rem;              /* 32px */
font-weight: 700;             /* Bold */
letter-spacing: -0.02em;      /* Tight */
line-height: 1.1;
```
Example: `<h1 className="font-mono text-3xl font-bold tracking-tight">Wage vs Essentials</h1>`

**H2 (Section Headers, Card Groups):**
```css
font-family: 'JetBrains Mono', monospace;
font-size: 1.5rem;            /* 24px */
font-weight: 600;             /* SemiBold */
letter-spacing: -0.01em;
line-height: 1.3;
```
Example: `<h2 className="font-mono text-2xl font-semibold tracking-tight">Price History</h2>`

**H3 (Card Titles, Subsections):**
```css
font-family: 'Inter', sans-serif;
font-size: 1.25rem;           /* 20px */
font-weight: 600;             /* SemiBold */
letter-spacing: 0;
line-height: 1.3;
```
Example: `<h3 className="text-xl font-semibold">Data Sources</h3>`

**Body (Primary Text):**
```css
font-family: 'Inter', sans-serif;
font-size: 1rem;              /* 16px */
font-weight: 400;             /* Regular */
letter-spacing: 0;
line-height: 1.5;
```
Example: `<p className="text-base">Chronos tracks...</p>`

**Small (Metadata, Labels, Captions):**
```css
font-family: 'Inter', sans-serif;
font-size: 0.875rem;          /* 14px */
font-weight: 400;
letter-spacing: 0;
line-height: 1.5;
```
Example: `<span className="text-sm text-text-secondary">Updated 2 hours ago</span>`

**Data Labels (Charts, Tables, Timestamps):**
```css
font-family: 'JetBrains Mono', monospace;
font-size: 0.875rem;          /* 14px */
font-weight: 500;             /* Medium */
letter-spacing: 0.01em;       /* Slightly wider for readability */
line-height: 1.4;
font-variant-numeric: tabular-nums;
```
Example: `<span className="font-mono text-sm font-medium">$3.45</span>`

**Large Metrics (Dashboard KPIs):**
```css
font-family: 'JetBrains Mono', monospace;
font-size: 3rem;              /* 48px */
font-weight: 700;             /* Bold */
letter-spacing: -0.01em;
line-height: 1.1;
font-variant-numeric: tabular-nums;
```
Example: `<div className="font-mono text-metric font-bold tracking-tight">15.2 hrs</div>`

### Usage Examples

```tsx
// Page title
<h1 className="font-mono text-3xl font-bold tracking-tight">
  Generational Dashboard
</h1>

// Section header
<h2 className="font-mono text-2xl font-semibold tracking-tight mb-4">
  Affordability Analysis
</h2>

// Card title
<h3 className="text-xl font-semibold mb-2">
  Minimum Wage vs Basket
</h3>

// Body text
<p className="text-base leading-normal">
  Purchasing power declined by 12.3% over the selected period.
</p>

// Metadata
<span className="text-sm text-text-secondary">
  Last updated: 2 hours ago
</span>

// Data display
<span className="font-mono text-sm font-medium tabular-nums">
  $3.45/lb
</span>

// Large metric
<div className="font-mono text-metric font-bold tabular-nums">
  15.2
</div>
<span className="font-mono text-base text-text-secondary">
  hours of work
</span>
```

---

## Brand Textures & Motifs

Subtle visual elements that reinforce the "forensic ledger" aesthetic without harming readability.

### Ledger Grid Background

**Purpose**: Add archival texture to panels and containers

**Implementation**:
```tsx
<div className="ledger-bg p-6">
  {/* Content */}
</div>
```

**CSS** (already defined in index.css):
```css
.ledger-bg {
  background-image: 
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 20px 20px;
}
```

**Usage**: Apply to surface-elevated elements, modal backgrounds, empty states. Avoid on busy areas or behind dense text.

### Engraved Divider

**Purpose**: Section separators with currency-style fine lines

**Implementation**:
```tsx
<div className="engraved-divider my-6" />
```

**CSS** (already defined in index.css):
```css
.engraved-divider {
  height: 3px;
  background-image: repeating-linear-gradient(
    0deg,
    var(--border),
    var(--border) 1px,
    transparent 1px,
    transparent 2px
  );
}
```

**Usage**: Between major page sections, above/below card groups, in modal headers.

### Mint Mark Seal

**Purpose**: Authentication indicator, data verification badge

**Implementation**:
```tsx
import { MintMarkIcon } from '@/components/brand-icons'

<div className="relative">
  {/* Card content */}
  <MintMarkIcon size={16} className="absolute bottom-2 right-2 text-accent opacity-40" />
</div>
```

**Usage**: 
- Bottom-right of verified data cards
- Adjacent to source citations
- In "last updated" timestamps
- Part of authentication UI

### Archival Stamp

**Purpose**: Verified source indicator, approval mark

**Implementation**:
```tsx
import { ArchivalStampIcon } from '@/components/brand-icons'

<ArchivalStampIcon size={24} className="text-accent" />
```

**Usage**:
- Next to verified data sources
- In methodology "approved by" sections
- Export download completion indicators

**Constraint**: All textures must remain subtle—never interfere with text readability or chart legibility.

---

## Chart Styling Guidelines

### Dark Background Charts

**Axes**:
```tsx
stroke: 'var(--chart-axis)'
strokeWidth: 1
font-family: 'Inter'
font-size: 12
fill: 'var(--text-secondary)'
```

**Gridlines**:
```tsx
stroke: 'var(--chart-grid)'
strokeWidth: 1
strokeDasharray: '4 4'
opacity: 0.6
```

**Series Lines** (with colorblind-safe patterns):
```tsx
// Series 1: Steel blue + solid
<path
  stroke="var(--chart-1)"
  strokeWidth={2}
  strokeDasharray="4 0"
  strokeLinecap="round"
  strokeLinejoin="round"
/>

// Series 2: Amber + dashed
<path
  stroke="var(--chart-2)"
  strokeWidth={2}
  strokeDasharray="8 4"
/>

// Series 3: Teal + dotted
<path
  stroke="var(--chart-3)"
  strokeWidth={2}
  strokeDasharray="2 4"
/>

// Series 4: Purple + dash-dot
<path
  stroke="var(--chart-4)"
  strokeWidth={2}
  strokeDasharray="8 4 2 4"
/>

// Series 5: Seafoam + long-dash
<path
  stroke="var(--chart-5)"
  strokeWidth={2}
  strokeDasharray="12 6"
/>
```

**Data Points**:
```tsx
<circle
  r={4}              // default
  r={6}              // hover
  fill="var(--chart-1)"
  stroke="var(--background)"
  strokeWidth={2}    // separation from line
/>
```

**Tooltips**:
```tsx
<div className="
  bg-surface-elevated
  border border-border-strong
  rounded-md
  shadow-lg
  p-3
  font-sans text-sm
">
  <div className="font-mono font-medium tabular-nums">
    $3.45
  </div>
  <div className="text-text-secondary text-xs">
    Jan 2020
  </div>
</div>
```

**Hover States**:
- Active series: Full opacity, strokeWidth 3px
- Inactive series: 40% opacity, strokeWidth 2px
- Focus ring on keyboard nav: 2px solid var(--accent)

### Accessibility Features

**Keyboard Navigation**:
- Tab through data points
- Arrow keys to move between series
- Enter to toggle series visibility
- Escape to clear selection

**Screen Reader Support**:
```tsx
<svg aria-label="Price history chart" role="img">
  <title>Price history from 2010 to 2024</title>
  <desc>
    Chart showing eggs price in dollars from $1.50 in 2010 
    increasing to $4.25 in 2024
  </desc>
  {/* Chart elements */}
</svg>

<!-- Hidden table alternative -->
<div className="sr-only">
  <table>
    <caption>Price history data</caption>
    <thead>
      <tr><th>Date</th><th>Price</th></tr>
    </thead>
    <tbody>
      <tr><td>2010</td><td>$1.50</td></tr>
      {/* ...more rows */}
    </tbody>
  </table>
</div>
```

**Colorblind-Safe Differentiation** (REQUIRED):
- Every chart series MUST have a unique line dash pattern
- Legend MUST show both color and dash pattern
- Data point shapes (circle, square, triangle) for overlapping series
- Never rely on color alone to convey information

---

### Brand Voice

**Educational** - Explains complex economic concepts clearly  
**Neutral** - Avoids political framing or blame  
**Transparent** - Shows all formulas, sources, and limitations  
**Empathetic** - Acknowledges different generational experiences  
**Rigorous** - Every claim backed by cited data

### Content Guidelines

✅ **DO:**
- Use "How did affordability differ between 1975 and 2005?"
- Present observed data patterns objectively
- Separate "What the data shows" from "What it doesn't show"
- Cite credible sources (NBER, Federal Reserve, BLS, academic)
- Label assumptions and methodology explicitly

❌ **DON'T:**
- Attribute intent to unnamed actors
- Present unverified claims as fact
- Use accusatory framing or blame language
- Mix interpretation with raw data
- Make predictions without disclaimers

---

## Design Patterns

### Cards
Primary container pattern with subtle borders, rounded corners (0.5rem), and shadow on hover

### Data Visualization
- Clean axes with clear labels and units
- Muted gridlines (30% opacity)
- Interactive hover states highlighting series
- Formula tooltips on all derived metrics
- "What it shows / doesn't show" guardrails

### Loading States
Skeleton screens with subtle pulse animation (no spinners)

### Status Indicators
- Color + icon + text (never color alone for accessibility)
- Verified sources: Accent color + VerifiedIcon
- Data gaps: Destructive + WarningIcon
- Neutral trends: Muted colors for increase/decrease

---

## Implementation

### Viewing the Icon System

Visit the icon showcase to see all icons in context:

```tsx
// In your browser, navigate to:
/#icons

// Or programmatically:
onTabChange('icons')
```

### Component Imports

```tsx
// Logo
import { Logo } from '@/components/Logo'

// Icons
import { 
  AnalyticsIcon, 
  GenerationsIcon, 
  AffordabilityIcon 
} from '@/components/icons'

// Usage in navigation
<AnalyticsIcon size={18} weight="bold" className="text-primary" />
```

---

## Brand Evolution

**Version:** 1.0  
**Date:** 2024  
**Status:** Active

### Future Considerations
- Animated logo variant for loading states
- Extended icon set for new features (utilities, rent, regional analysis)
- Print/PDF export templates with brand system
- Educator materials kit with branded templates

---

## Contact & Questions

For brand usage questions or custom implementation needs, refer to the PRD.md for product direction and component documentation for technical implementation.

**Remember:** Every design decision should reinforce transparency, build trust, and foster cross-generational understanding.
