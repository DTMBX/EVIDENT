import { Card } from '@/components/ui/card'
import { Logo } from '@/components/Logo'
import {
  TimelineIcon,
  GenerationsIcon,
  AffordabilityIcon,
  VolatilityIcon,
  BasketIcon,
  InsightIcon,
  CompareIcon,
  DataSourceIcon,
  MethodologyIcon,
  ExploreIcon,
  AnalyticsIcon,
  RefreshIcon,
  SettingsIcon,
  ShareIcon,
  HomeIcon,
  TrendUpIcon,
  TrendDownIcon,
  ClockIcon,
  EducationIcon,
  DialogueIcon,
  WarningIcon,
  VerifiedIcon,
  FilterIcon,
  ExportIcon,
  CalendarIcon,
} from '@/components/icons'

const iconSets = [
  {
    category: 'Brand',
    icons: [
      { name: 'Logo', component: Logo, description: 'Primary brand mark', isLogo: true },
    ]
  },
  {
    category: 'Navigation',
    icons: [
      { name: 'Home', component: HomeIcon, description: 'Dashboard home' },
      { name: 'Explore', component: ExploreIcon, description: 'Browse items' },
      { name: 'Compare', component: CompareIcon, description: 'Chart builder' },
      { name: 'Analytics', component: AnalyticsIcon, description: 'Analytics view' },
      { name: 'Settings', component: SettingsIcon, description: 'Configuration' },
    ]
  },
  {
    category: 'Features',
    icons: [
      { name: 'Timeline', component: TimelineIcon, description: 'Historical timeline' },
      { name: 'Generations', component: GenerationsIcon, description: 'Generational analysis' },
      { name: 'Affordability', component: AffordabilityIcon, description: 'Hours of work' },
      { name: 'Volatility', component: VolatilityIcon, description: 'Price stability' },
      { name: 'Basket', component: BasketIcon, description: 'Essential goods' },
      { name: 'Insight', component: InsightIcon, description: 'Key findings' },
      { name: 'Education', component: EducationIcon, description: 'Learning module' },
      { name: 'Dialogue', component: DialogueIcon, description: 'Discussion prompts' },
    ]
  },
  {
    category: 'Data & Sources',
    icons: [
      { name: 'DataSource', component: DataSourceIcon, description: 'API sources' },
      { name: 'Methodology', component: MethodologyIcon, description: 'Formulas' },
      { name: 'Refresh', component: RefreshIcon, description: 'Update data' },
      { name: 'Verified', component: VerifiedIcon, description: 'Credible source' },
      { name: 'Warning', component: WarningIcon, description: 'Data gap' },
    ]
  },
  {
    category: 'Actions',
    icons: [
      { name: 'Share', component: ShareIcon, description: 'Share config' },
      { name: 'Export', component: ExportIcon, description: 'Download data' },
      { name: 'Filter', component: FilterIcon, description: 'Filter options' },
      { name: 'Calendar', component: CalendarIcon, description: 'Date range' },
    ]
  },
  {
    category: 'Indicators',
    icons: [
      { name: 'TrendUp', component: TrendUpIcon, description: 'Price increase' },
      { name: 'TrendDown', component: TrendDownIcon, description: 'Price decrease' },
      { name: 'Clock', component: ClockIcon, description: 'Time metric' },
    ]
  },
]

export function IconShowcase() {
  return (
    <div className="space-y-12 py-8">
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="text-primary">
            <Logo size={64} />
          </div>
          <div>
            <h1 className="font-display font-bold text-4xl">Chronos</h1>
            <p className="text-xl text-muted-foreground">Generational Economic Insights</p>
          </div>
        </div>
        <p className="text-muted-foreground max-w-2xl">
          A comprehensive icon system designed to represent generational economic analysis, 
          time-series data, and transparent research methodology.
        </p>
      </div>

      {iconSets.map((set) => (
        <div key={set.category} className="space-y-4">
          <div>
            <h2 className="font-display font-bold text-2xl">{set.category}</h2>
            <p className="text-sm text-muted-foreground">
              {set.icons.length} icon{set.icons.length !== 1 ? 's' : ''}
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {set.icons.map((icon) => {
              const IconComponent = icon.component
              return (
                <Card key={icon.name} className="p-4 hover:shadow-md transition-shadow">
                  <div className="space-y-3">
                    {icon.isLogo ? (
                      <div className="flex items-center justify-center">
                        <div className="text-primary">
                          <IconComponent size={42} />
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-4">
                        <div className="text-muted-foreground">
                          <IconComponent size={28} weight="thin" />
                        </div>
                        <div className="text-foreground">
                          <IconComponent size={28} weight="regular" />
                        </div>
                        <div className="text-primary">
                          <IconComponent size={28} weight="bold" />
                        </div>
                      </div>
                    )}
                    <div className="space-y-1">
                      <p className="font-mono font-semibold text-sm">{icon.name}</p>
                      <p className="text-xs text-muted-foreground leading-snug">
                        {icon.description}
                      </p>
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        </div>
      ))}

      <div className="border-t pt-8 space-y-4">
        <h2 className="font-display font-bold text-2xl">Usage Examples</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="p-6 space-y-4">
            <h3 className="font-display font-semibold text-lg">Weight Variants</h3>
            <div className="flex items-center gap-6">
              <div className="space-y-2 text-center">
                <div className="text-muted-foreground"><AnalyticsIcon size={32} weight="thin" /></div>
                <p className="text-xs font-mono">thin</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-foreground"><AnalyticsIcon size={32} weight="regular" /></div>
                <p className="text-xs font-mono">regular</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-primary"><AnalyticsIcon size={32} weight="bold" /></div>
                <p className="text-xs font-mono">bold</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="font-display font-semibold text-lg">Size Variants</h3>
            <div className="flex items-center gap-6">
              <div className="space-y-2 text-center">
                <div className="text-primary"><GenerationsIcon size={16} weight="regular" /></div>
                <p className="text-xs font-mono">16px</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-primary"><GenerationsIcon size={24} weight="regular" /></div>
                <p className="text-xs font-mono">24px</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-primary"><GenerationsIcon size={32} weight="regular" /></div>
                <p className="text-xs font-mono">32px</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-primary"><GenerationsIcon size={48} weight="regular" /></div>
                <p className="text-xs font-mono">48px</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="font-display font-semibold text-lg">Color Variations</h3>
            <div className="flex items-center gap-6">
              <div className="space-y-2 text-center">
                <div className="text-primary"><VolatilityIcon size={32} weight="regular" /></div>
                <p className="text-xs font-mono">primary</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-accent"><VolatilityIcon size={32} weight="regular" /></div>
                <p className="text-xs font-mono">accent</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-muted-foreground"><VolatilityIcon size={32} weight="regular" /></div>
                <p className="text-xs font-mono">muted</p>
              </div>
              <div className="space-y-2 text-center">
                <div className="text-destructive"><VolatilityIcon size={32} weight="regular" /></div>
                <p className="text-xs font-mono">destructive</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="font-display font-semibold text-lg">Contextual Usage</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <TrendUpIcon size={18} weight="regular" className="text-increase" />
                <span>Price increased 12.5%</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <TrendDownIcon size={18} weight="regular" className="text-decrease" />
                <span>Volatility decreased</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <VerifiedIcon size={18} weight="regular" className="text-accent" />
                <span>Source verified</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <WarningIcon size={18} weight="regular" className="text-destructive" />
                <span>Data gap detected</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
