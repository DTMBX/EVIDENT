import { Card } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Clock, 
  CalendarBlank, 
  HandPointing,
  CheckCircle,
  Info
} from '@phosphor-icons/react'
import type { RefreshSchedule } from '@/lib/types'
import { getScheduleLabel, formatRefreshTimestamp } from '@/lib/data-refresh'

interface RefreshScheduleSettingsProps {
  schedule: RefreshSchedule
  autoRefreshEnabled: boolean
  nextScheduledRefresh?: string
  lastScheduledRefresh?: string
  onScheduleChange: (schedule: RefreshSchedule) => void
  onToggleAutoRefresh: (enabled: boolean) => void
}

export function RefreshScheduleSettings({
  schedule,
  autoRefreshEnabled,
  nextScheduledRefresh,
  lastScheduledRefresh,
  onScheduleChange,
  onToggleAutoRefresh
}: RefreshScheduleSettingsProps) {
  const getScheduleIcon = (sched: RefreshSchedule) => {
    switch (sched) {
      case 'hourly':
        return <Clock size={16} />
      case 'daily':
        return <CalendarBlank size={16} />
      case 'manual':
        return <HandPointing size={16} />
      default:
        return <Clock size={16} />
    }
  }

  const getScheduleDescription = (sched: RefreshSchedule): string => {
    switch (sched) {
      case 'hourly':
        return 'Data sources will be refreshed automatically at the start of every hour'
      case 'daily':
        return 'Data sources will be refreshed once per day at 2:00 AM local time'
      case 'manual':
        return 'Data sources will only be refreshed when you manually trigger a refresh'
      case 'disabled':
        return 'All automatic refresh operations are disabled'
      default:
        return ''
    }
  }

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Auto-Refresh Schedule</h2>
          <p className="text-sm text-muted-foreground">
            Configure automatic data source updates to keep your price and wage information current
          </p>
        </div>

        <div className="flex items-center justify-between gap-4 p-4 rounded-lg bg-accent/10 border border-accent/20">
          <div className="flex-1">
            <Label htmlFor="auto-refresh-toggle" className="text-base font-medium cursor-pointer">
              Enable Auto-Refresh
            </Label>
            <p className="text-sm text-muted-foreground mt-1">
              Automatically update data sources based on the schedule below
            </p>
          </div>
          <Switch
            id="auto-refresh-toggle"
            checked={autoRefreshEnabled}
            onCheckedChange={onToggleAutoRefresh}
          />
        </div>

        <div className="space-y-3">
          <Label>Refresh Frequency</Label>
          <Select 
            value={schedule} 
            onValueChange={(v) => onScheduleChange(v as RefreshSchedule)}
            disabled={!autoRefreshEnabled}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="manual">
                <div className="flex items-center gap-2">
                  <HandPointing size={16} />
                  <span>Manual Only</span>
                </div>
              </SelectItem>
              <SelectItem value="hourly">
                <div className="flex items-center gap-2">
                  <Clock size={16} />
                  <span>Every Hour</span>
                </div>
              </SelectItem>
              <SelectItem value="daily">
                <div className="flex items-center gap-2">
                  <CalendarBlank size={16} />
                  <span>Daily at 2:00 AM</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
          
          {autoRefreshEnabled && (
            <Alert>
              <Info size={16} />
              <AlertDescription className="text-sm">
                {getScheduleDescription(schedule)}
              </AlertDescription>
            </Alert>
          )}
        </div>

        {autoRefreshEnabled && schedule !== 'manual' && schedule !== 'disabled' && (
          <div className="space-y-3 p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1.5">
                <CheckCircle size={14} weight="fill" />
                Active Schedule
              </Badge>
              <span className="text-sm font-medium">
                {getScheduleLabel(schedule)}
              </span>
            </div>

            {nextScheduledRefresh && (
              <div className="flex items-start gap-2 text-sm">
                <Clock size={16} className="text-muted-foreground flex-shrink-0 mt-0.5" />
                <div>
                  <span className="text-muted-foreground">Next scheduled refresh: </span>
                  <span className="font-medium text-foreground">
                    {formatRefreshTimestamp(nextScheduledRefresh)}
                  </span>
                </div>
              </div>
            )}

            {lastScheduledRefresh && (
              <div className="flex items-start gap-2 text-sm">
                <CheckCircle size={16} className="text-muted-foreground flex-shrink-0 mt-0.5" />
                <div>
                  <span className="text-muted-foreground">Last scheduled refresh: </span>
                  <span className="font-medium text-foreground">
                    {formatRefreshTimestamp(lastScheduledRefresh)}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="pt-4 border-t space-y-3">
          <h3 className="font-semibold text-sm">Schedule Recommendations</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <Clock size={16} className="flex-shrink-0 mt-0.5 text-primary" />
              <div>
                <span className="font-medium text-foreground">Hourly:</span> Best for active 
                monitoring and time-sensitive analysis. Recommended for users tracking volatile commodities.
              </div>
            </li>
            <li className="flex items-start gap-2">
              <CalendarBlank size={16} className="flex-shrink-0 mt-0.5 text-primary" />
              <div>
                <span className="font-medium text-foreground">Daily:</span> Balanced approach 
                suitable for most use cases. Minimal resource usage with up-to-date data.
              </div>
            </li>
            <li className="flex items-start gap-2">
              <HandPointing size={16} className="flex-shrink-0 mt-0.5 text-primary" />
              <div>
                <span className="font-medium text-foreground">Manual:</span> Full control over 
                when data updates occur. Recommended when working with cached datasets.
              </div>
            </li>
          </ul>
        </div>
      </div>
    </Card>
  )
}
