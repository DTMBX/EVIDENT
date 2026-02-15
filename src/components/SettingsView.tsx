import { Card } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useState } from 'react'
import { useKV } from '@github/spark/hooks'
import type { UserWageConfig, RefreshScheduleConfig } from '@/lib/types'
import { getScheduleLabel } from '@/lib/data-refresh'
import { toast } from 'sonner'
import { CheckCircle, Clock } from '@phosphor-icons/react'

interface SettingsViewProps {
  wageConfig: UserWageConfig
  onUpdateWage: (config: UserWageConfig) => void
}

export function SettingsView({ wageConfig, onUpdateWage }: SettingsViewProps) {
  const [localConfig, setLocalConfig] = useState<UserWageConfig>(wageConfig)
  const [customWage, setCustomWage] = useState(wageConfig.hourlyWage?.toString() || '15.00')
  
  const [scheduleConfig] = useKV<RefreshScheduleConfig>('refresh-schedule-config', {
    enabled: true,
    schedule: 'manual',
    autoRefreshEnabled: false
  })

  const handleSave = () => {
    const updatedConfig: UserWageConfig = {
      ...localConfig,
      hourlyWage: localConfig.type === 'manual' ? parseFloat(customWage) : undefined
    }
    onUpdateWage(updatedConfig)
    toast.success('Settings saved', {
      description: 'Your wage configuration has been updated'
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Configure wage assumptions and regional preferences
        </p>
      </div>

      {scheduleConfig && scheduleConfig.autoRefreshEnabled && (
        <Card className="p-4 bg-accent/10 border-accent">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-full bg-accent/20 text-accent">
              {scheduleConfig.schedule === 'manual' ? (
                <Clock size={20} />
              ) : (
                <CheckCircle size={20} weight="fill" />
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">
                Auto-Refresh: {scheduleConfig.schedule !== 'manual' && scheduleConfig.schedule !== 'disabled' ? 'Active' : 'Manual Mode'}
              </p>
              <p className="text-xs text-muted-foreground">
                Schedule: {getScheduleLabel(scheduleConfig.schedule)}
              </p>
            </div>
            <Badge variant="outline" className="gap-1.5">
              <CheckCircle size={12} weight="fill" />
              Enabled
            </Badge>
          </div>
        </Card>
      )}

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Wage Configuration</h2>
        
        <div className="space-y-6">
          <div className="space-y-2">
            <Label>Wage Source Type</Label>
            <Select 
              value={localConfig.type} 
              onValueChange={(v) => setLocalConfig({ ...localConfig, type: v as 'manual' | 'sourced' })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="manual">Manual Entry</SelectItem>
                <SelectItem value="sourced">Government Data Series</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Choose between entering your own hourly wage or using official wage statistics
            </p>
          </div>

          {localConfig.type === 'manual' ? (
            <div className="space-y-2">
              <Label htmlFor="hourly-wage">Hourly Wage (USD)</Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    $
                  </span>
                  <Input
                    id="hourly-wage"
                    type="number"
                    step="0.01"
                    min="0"
                    value={customWage}
                    onChange={(e) => setCustomWage(e.target.value)}
                    className="pl-7 font-mono"
                  />
                </div>
                <span className="flex items-center text-muted-foreground">/hour</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Enter your hourly wage or salary converted to hourly rate
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <Label>Wage Series</Label>
              <Select 
                value={localConfig.sourcedSeriesId || 'minimum'} 
                onValueChange={(v) => setLocalConfig({ ...localConfig, sourcedSeriesId: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="minimum">Federal Minimum Wage</SelectItem>
                  <SelectItem value="median">Median Hourly Earnings</SelectItem>
                  <SelectItem value="sector-retail">Retail Sector Average</SelectItem>
                  <SelectItem value="sector-manufacturing">Manufacturing Sector Average</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Select a government-tracked wage series from Bureau of Labor Statistics
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label>Region</Label>
            <Select 
              value={localConfig.region} 
              onValueChange={(v) => setLocalConfig({ ...localConfig, region: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="US-National">United States (National)</SelectItem>
                <SelectItem value="US-Northeast">Northeast Region</SelectItem>
                <SelectItem value="US-Midwest">Midwest Region</SelectItem>
                <SelectItem value="US-South">South Region</SelectItem>
                <SelectItem value="US-West">West Region</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Regional data availability may vary by item
            </p>
          </div>

          <div className="pt-4 border-t">
            <Button onClick={handleSave}>
              Save Configuration
            </Button>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">About Wage Calculations</h2>
        <div className="space-y-3 text-sm text-muted-foreground">
          <p>
            <span className="font-medium text-foreground">Hours of Work</span> is calculated as:
          </p>
          <div className="bg-muted p-3 rounded font-mono text-xs">
            hours_of_work = (price_per_unit × quantity) ÷ hourly_wage
          </div>
          <p>
            This metric helps compare affordability across time periods by normalizing prices 
            against earning power. A lower hours-of-work value means an item is more affordable 
            relative to wages.
          </p>
          <p>
            <span className="font-medium text-foreground">Salary to Hourly Conversion:</span> If 
            entering a salary, divide annual salary by 2,080 (52 weeks × 40 hours) for a standard 
            full-time hourly rate.
          </p>
        </div>
      </Card>

      <Card className="p-6 bg-accent/10 border-accent">
        <h3 className="font-semibold mb-2">Data Transparency</h3>
        <p className="text-sm text-muted-foreground">
          When using government wage series, the source and retrieval timestamp are displayed 
          alongside all calculations. Manual wage entries are clearly labeled in all exports 
          and visualizations to maintain methodological transparency.
        </p>
      </Card>
    </div>
  )
}
