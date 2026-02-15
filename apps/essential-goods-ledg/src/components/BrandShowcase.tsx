import { Card } from '@/components/ui/card'
import { Logo, LogoIcon, LogoLockup, LogoSpinner, LogoPulse } from '@/components/Logo'
import {
  HeadstoneIcon,
  LedgerIcon,
  MintMarkIcon,
  ArchivalStampIcon,
  DecayLineIcon,
  FlatlineIcon,
  GridPatternIcon,
  EngravedLineIcon,
  ForensicIcon,
  TruthIcon,
  EvidenceIcon,
  HourglassDecayIcon,
  ArchiveBoxIcon
} from '@/components/brand-icons'

export function BrandShowcase() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div className="space-y-3">
        <h1 className="font-mono text-3xl font-bold tracking-tight">
          Chronos Visual Identity
        </h1>
        <p className="text-base text-text-secondary">
          Dark-truth brand system: forensic, accessible, non-partisan
        </p>
      </div>

      <div className="engraved-divider" />

      <section className="space-y-4">
        <h2 className="font-mono text-2xl font-semibold tracking-tight">Logo System</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Primary Logo</h3>
            <div className="flex items-center justify-center py-8 bg-surface rounded-lg">
              <Logo size={80} className="text-foreground" />
            </div>
            <p className="text-sm text-text-secondary">
              Headstone marker with sparkline, grid, and seal
            </p>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Icon Square</h3>
            <div className="flex items-center justify-center py-8 bg-surface rounded-lg">
              <LogoIcon size={80} variant="square" className="text-primary" />
            </div>
            <p className="text-sm text-text-secondary">
              For app icons, favicons
            </p>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Icon Circle</h3>
            <div className="flex items-center justify-center py-8 bg-surface rounded-lg">
              <LogoIcon size={80} variant="circle" className="text-accent" />
            </div>
            <p className="text-sm text-text-secondary">
              For avatars, badges
            </p>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Logo Lockup</h3>
            <div className="flex items-center justify-center py-8 bg-surface rounded-lg">
              <LogoLockup height={48} className="text-foreground" />
            </div>
            <p className="text-sm text-text-secondary">
              Horizontal icon + wordmark
            </p>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Spinner (Loading)</h3>
            <div className="flex items-center justify-center py-8 bg-surface rounded-lg">
              <LogoSpinner size={64} className="text-primary" />
            </div>
            <p className="text-sm text-text-secondary">
              Infinite loop, sparkline oscillates
            </p>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Pulse (Loading)</h3>
            <div className="flex items-center justify-center py-8 bg-surface rounded-lg">
              <LogoPulse size={64} className="text-accent" />
            </div>
            <p className="text-sm text-text-secondary">
              Slow pulse, purchasing power decay
            </p>
          </Card>
        </div>
      </section>

      <div className="engraved-divider" />

      <section className="space-y-4">
        <h2 className="font-mono text-2xl font-semibold tracking-tight">Brand Icons</h2>
        <p className="text-base text-text-secondary">
          Forensic ledger aesthetic with consistent 24×24 grid, 2px strokes, rounded joins
        </p>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {[
            { icon: HeadstoneIcon, name: 'Headstone', desc: 'Monument marker' },
            { icon: LedgerIcon, name: 'Ledger', desc: 'Accounting grid' },
            { icon: MintMarkIcon, name: 'Mint Mark', desc: 'Authentication seal' },
            { icon: ArchivalStampIcon, name: 'Stamp', desc: 'Verified badge' },
            { icon: DecayLineIcon, name: 'Decay Line', desc: 'Declining trend' },
            { icon: FlatlineIcon, name: 'Flatline', desc: 'Stagnation' },
            { icon: GridPatternIcon, name: 'Grid Pattern', desc: 'Ledger structure' },
            { icon: EngravedLineIcon, name: 'Engraved', desc: 'Fine dividers' },
            { icon: ForensicIcon, name: 'Forensic', desc: 'Data investigation' },
            { icon: TruthIcon, name: 'Truth', desc: 'Evidence shield' },
            { icon: EvidenceIcon, name: 'Evidence', desc: 'Document analysis' },
            { icon: HourglassDecayIcon, name: 'Time Decay', desc: 'Purchasing power' },
            { icon: ArchiveBoxIcon, name: 'Archive', desc: 'Historical data' },
          ].map(({ icon: Icon, name, desc }) => (
            <Card key={name} className="p-4 space-y-3 hover:border-accent transition-colors">
              <div className="flex items-center justify-center py-4 bg-surface rounded">
                <Icon size={32} className="text-foreground" />
              </div>
              <div className="space-y-1">
                <p className="font-medium text-sm">{name}</p>
                <p className="text-xs text-text-muted">{desc}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <div className="engraved-divider" />

      <section className="space-y-4">
        <h2 className="font-mono text-2xl font-semibold tracking-tight">Color System</h2>
        
        <div className="space-y-6">
          <div className="space-y-3">
            <h3 className="text-lg font-semibold">Dark Theme (Default)</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {[
                { name: 'Background', var: '--background', text: '--foreground' },
                { name: 'Surface', var: '--surface', text: '--foreground' },
                { name: 'Surface Elevated', var: '--surface-elevated', text: '--foreground' },
                { name: 'Primary', var: '--primary', text: '--primary-foreground' },
                { name: 'Accent', var: '--accent', text: '--accent-foreground' },
                { name: 'Success', var: '--success', text: '--foreground' },
                { name: 'Warning', var: '--warning', text: '--foreground' },
                { name: 'Danger', var: '--danger', text: '--foreground' },
                { name: 'Chart 1', var: '--chart-1', text: '--foreground' },
                { name: 'Chart 2', var: '--chart-2', text: '--foreground' },
              ].map(({ name, var: cssVar, text }) => (
                <div key={name} className="space-y-2">
                  <div
                    className="h-20 rounded border border-border flex items-center justify-center font-mono text-xs font-medium"
                    style={{
                      backgroundColor: `var(${cssVar})`,
                      color: `var(${text})`
                    }}
                  >
                    {name}
                  </div>
                  <p className="text-xs text-text-secondary font-mono">{cssVar}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="engraved-divider" />

      <section className="space-y-4">
        <h2 className="font-mono text-2xl font-semibold tracking-tight">Typography</h2>
        
        <Card className="p-6 space-y-6">
          <div className="space-y-2">
            <p className="text-sm text-text-secondary font-mono">JetBrains Mono Bold · 32px · -0.02em</p>
            <h1 className="font-mono text-3xl font-bold tracking-tight">
              The forensic ledger of purchasing power
            </h1>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-text-secondary font-mono">JetBrains Mono SemiBold · 24px · -0.01em</p>
            <h2 className="font-mono text-2xl font-semibold tracking-tight">
              Data reveals the slow decay of affordability
            </h2>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-text-secondary font-mono">Inter SemiBold · 20px · 0</p>
            <h3 className="text-xl font-semibold">
              Evidence-driven insights for all generations
            </h3>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-text-secondary font-mono">Inter Regular · 16px · 0 · 1.5 line-height</p>
            <p className="text-base">
              Chronos tracks essential goods prices and wages across decades, converting cost into hours of work. 
              The platform promotes civic literacy and respectful dialogue through transparent data exploration 
              rather than blame or division.
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-text-secondary font-mono">Inter Regular · 14px · Metadata</p>
            <p className="text-sm text-text-secondary">
              Last updated: 2 hours ago · Source: Bureau of Labor Statistics · Coverage: 95%
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-text-secondary font-mono">JetBrains Mono Medium · 14px · Tabular Nums</p>
            <div className="flex gap-4 font-mono text-sm font-medium tabular-nums">
              <span>$3.45</span>
              <span>$12.89</span>
              <span>$156.23</span>
              <span>15.2 hrs</span>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-text-secondary font-mono">JetBrains Mono Bold · 48px · Dashboard Metric</p>
            <div className="font-mono text-metric font-bold tabular-nums">
              15.2
            </div>
            <p className="font-mono text-base text-text-secondary">hours of work</p>
          </div>
        </Card>
      </section>

      <div className="engraved-divider" />

      <section className="space-y-4">
        <h2 className="font-mono text-2xl font-semibold tracking-tight">Brand Textures</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Ledger Grid Background</h3>
            <div className="ledger-bg h-32 rounded border border-border flex items-center justify-center">
              <p className="font-mono text-sm text-text-secondary">Subtle accounting grid texture</p>
            </div>
            <p className="text-sm text-text-secondary">
              Apply to surface-elevated elements and modal backgrounds
            </p>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Engraved Divider</h3>
            <div className="space-y-6">
              <p className="text-sm text-text-secondary">
                Fine parallel lines inspired by currency engraving
              </p>
              <div className="engraved-divider" />
              <p className="text-sm text-text-secondary">
                Use between major sections and in modal headers
              </p>
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Mint Mark Seal</h3>
            <div className="relative bg-surface rounded p-8">
              <p className="text-sm text-text-secondary">Verified data container</p>
              <MintMarkIcon size={20} className="absolute bottom-2 right-2 text-accent opacity-40" />
            </div>
            <p className="text-sm text-text-secondary">
              Place in bottom-right of verified data cards
            </p>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-semibold">Archival Stamp</h3>
            <div className="flex items-center justify-center py-8 bg-surface rounded">
              <ArchivalStampIcon size={48} className="text-accent" />
            </div>
            <p className="text-sm text-text-secondary">
              Use for verified sources and approved methodologies
            </p>
          </Card>
        </div>
      </section>

      <div className="engraved-divider" />

      <section className="space-y-4">
        <h2 className="font-mono text-2xl font-semibold tracking-tight">Chart Line Styles</h2>
        <p className="text-base text-text-secondary">
          Colorblind-safe differentiation: Each series uses distinct dash pattern + color
        </p>
        
        <Card className="p-6">
          <svg width="100%" height="200" viewBox="0 0 800 200" className="w-full">
            <defs>
              {[1, 2, 3, 4, 5].map(i => (
                <line key={`ref-${i}`} x1="0" y1={30 * i} x2="800" y2={30 * i} stroke="var(--chart-grid)" strokeWidth="0.5" opacity="0.3" />
              ))}
            </defs>
            
            <path d="M 50 150 L 200 120 L 350 140 L 500 100 L 650 110 L 750 90" 
              stroke="var(--chart-1)" strokeWidth="2.5" fill="none" strokeDasharray="4 0" strokeLinecap="round" />
            <text x="760" y="95" fill="var(--chart-1)" fontSize="12" fontFamily="Inter">Chart 1: Solid</text>
            
            <path d="M 50 140 L 200 110 L 350 130 L 500 95 L 650 105 L 750 85" 
              stroke="var(--chart-2)" strokeWidth="2.5" fill="none" strokeDasharray="8 4" strokeLinecap="round" />
            <text x="760" y="90" fill="var(--chart-2)" fontSize="12" fontFamily="Inter">Chart 2: Dashed</text>
            
            <path d="M 50 130 L 200 100 L 350 120 L 500 90 L 650 100 L 750 80" 
              stroke="var(--chart-3)" strokeWidth="2.5" fill="none" strokeDasharray="2 4" strokeLinecap="round" />
            <text x="760" y="85" fill="var(--chart-3)" fontSize="12" fontFamily="Inter">Chart 3: Dotted</text>
            
            <path d="M 50 120 L 200 90 L 350 110 L 500 85 L 650 95 L 750 75" 
              stroke="var(--chart-4)" strokeWidth="2.5" fill="none" strokeDasharray="8 4 2 4" strokeLinecap="round" />
            <text x="760" y="80" fill="var(--chart-4)" fontSize="12" fontFamily="Inter">Chart 4: Dash-dot</text>
            
            <path d="M 50 110 L 200 80 L 350 100 L 500 80 L 650 90 L 750 70" 
              stroke="var(--chart-5)" strokeWidth="2.5" fill="none" strokeDasharray="12 6" strokeLinecap="round" />
            <text x="760" y="75" fill="var(--chart-5)" fontSize="12" fontFamily="Inter">Chart 5: Long-dash</text>
          </svg>
        </Card>
      </section>

      <div className="engraved-divider" />

      <section className="space-y-4">
        <h2 className="font-mono text-2xl font-semibold tracking-tight">Brand Philosophy</h2>
        
        <Card className="p-6 space-y-4">
          <div className="space-y-2">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <TruthIcon size={20} className="text-accent" />
              Data Truth, Not Ideology
            </h3>
            <p className="text-base">
              Every visualization traces back to cited sources. We separate observed patterns from interpretation, 
              label all assumptions explicitly, and present "what the data shows" alongside "what it cannot prove."
            </p>
          </div>

          <div className="engraved-divider" />

          <div className="space-y-2">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <ForensicIcon size={20} className="text-primary" />
              Forensic Precision
            </h3>
            <p className="text-base">
              The visual language evokes archival ledgers, currency engraving, and authentication seals. 
              Dark-theme-first with high contrast ensures extreme legibility for data-intensive analysis.
            </p>
          </div>

          <div className="engraved-divider" />

          <div className="space-y-2">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <EvidenceIcon size={20} className="text-accent" />
              Non-Partisan Evidence
            </h3>
            <p className="text-base">
              We document purchasing power decline without blame. The headstone/marker logo symbolizes 
              the slow decay of affordability—a mathematical reality, not a political statement.
            </p>
          </div>
        </Card>
      </section>

      <div className="my-12" />
    </div>
  )
}
