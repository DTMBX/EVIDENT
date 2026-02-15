import { Logo, LogoSpinner, LogoPulse } from './Logo'
import { Card } from './ui/card'
import { LoadingStateExample } from './LoadingStateExample'

export function FullPageLoader() {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="flex flex-col items-center gap-4">
        <Logo animated size={64} className="text-primary" />
        <p className="text-sm text-muted-foreground font-medium">Loading...</p>
      </div>
    </div>
  )
}

export function InlineLoader({ size = 40, text }: { size?: number; text?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-8">
      <LogoSpinner size={size} className="text-primary" />
      {text && <p className="text-sm text-muted-foreground">{text}</p>}
    </div>
  )
}

export function CardLoader({ text }: { text?: string }) {
  return (
    <Card className="p-8">
      <div className="flex flex-col items-center gap-4">
        <LogoPulse size={48} className="text-primary" />
        {text && <p className="text-sm text-muted-foreground text-center">{text}</p>}
      </div>
    </Card>
  )
}

export function CompactLoader({ size = 24 }: { size?: number }) {
  return (
    <LogoSpinner size={size} className="text-primary" />
  )
}

export function DataRefreshLoader() {
  return (
    <div className="flex items-center gap-2 text-sm">
      <LogoSpinner size={20} className="text-accent" />
      <span className="text-muted-foreground">Refreshing data...</span>
    </div>
  )
}

export function LoadingShowcase() {
  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold font-display mb-2">Loading States Showcase</h1>
        <p className="text-muted-foreground">
          Animated logo variants for different loading scenarios
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Animated Logo</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Draw-in animation for page loads
          </p>
          <div className="flex justify-center py-4">
            <Logo animated size={64} className="text-primary" />
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Logo Spinner</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Circular spinner for async operations
          </p>
          <div className="flex justify-center py-4">
            <LogoSpinner size={64} className="text-primary" />
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Logo Pulse</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Pulsing animation for data updates
          </p>
          <div className="flex justify-center py-4">
            <LogoPulse size={64} className="text-primary" />
          </div>
        </Card>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold font-display mb-4">Usage Examples</h2>
        </div>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Full Page Loader</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Use for initial page loads or major transitions
          </p>
          <div className="relative bg-muted/30 rounded-lg p-8 min-h-[200px]">
            <div className="flex flex-col items-center justify-center gap-4 h-full">
              <Logo animated size={64} className="text-primary" />
              <p className="text-sm text-muted-foreground font-medium">Loading...</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Inline Loader</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Use for inline content loading within sections
          </p>
          <div className="bg-muted/30 rounded-lg p-8">
            <InlineLoader text="Loading chart data..." />
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Card Loader</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Use when loading content within a card component
          </p>
          <div className="bg-muted/30 rounded-lg p-8">
            <CardLoader text="Fetching analytics..." />
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Compact Loader</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Small spinner for buttons and tight spaces
          </p>
          <div className="bg-muted/30 rounded-lg p-6 flex items-center gap-4">
            <CompactLoader size={20} />
            <span className="text-sm">Processing...</span>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Data Refresh Loader</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Use when refreshing data sources
          </p>
          <div className="bg-muted/30 rounded-lg p-6">
            <DataRefreshLoader />
          </div>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-bold font-display">Size Variations</h2>
        <Card className="p-6">
          <div className="flex items-center gap-8 flex-wrap justify-center">
            <div className="flex flex-col items-center gap-2">
              <LogoSpinner size={16} className="text-primary" />
              <span className="text-xs text-muted-foreground">16px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <LogoSpinner size={24} className="text-primary" />
              <span className="text-xs text-muted-foreground">24px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <LogoSpinner size={32} className="text-primary" />
              <span className="text-xs text-muted-foreground">32px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <LogoSpinner size={48} className="text-primary" />
              <span className="text-xs text-muted-foreground">48px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <LogoSpinner size={64} className="text-primary" />
              <span className="text-xs text-muted-foreground">64px</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <LogoSpinner size={96} className="text-primary" />
              <span className="text-xs text-muted-foreground">96px</span>
            </div>
          </div>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-bold font-display">Implementation</h2>
        <Card className="p-6 bg-muted/50">
          <pre className="text-sm overflow-x-auto">
            <code>{`// Import the logo components
import { Logo, LogoSpinner, LogoPulse } from '@/components/Logo'
import { FullPageLoader, InlineLoader, CardLoader } from '@/components/LoadingStates'

// Use animated logo on initial load
<Logo animated size={64} className="text-primary" />

// Use spinner for async operations
<LogoSpinner size={40} className="text-primary" />

// Use pulse for data updates
<LogoPulse size={48} className="text-primary" />

// Use pre-built loading components
<FullPageLoader />
<InlineLoader text="Loading data..." />
<CardLoader text="Fetching analytics..." />
<CompactLoader size={20} />
<DataRefreshLoader />`}</code>
          </pre>
        </Card>
      </div>

      <LoadingStateExample />
    </div>
  )
}
