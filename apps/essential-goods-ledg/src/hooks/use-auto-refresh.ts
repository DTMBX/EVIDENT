import { useEffect, useRef, useCallback } from 'react'
import { useKV } from '@github/spark/hooks'
import { 
  refreshAllDataSources, 
  shouldRefresh,
  calculateNextRefresh,
  type RefreshMetadata 
} from '@/lib/data-refresh'
import type { RefreshSchedule, RefreshScheduleConfig } from '@/lib/types'
import type { Source } from '@/lib/types'
import { toast } from 'sonner'

interface UseAutoRefreshOptions {
  sources: Source[]
  onRefreshComplete?: (metadata: RefreshMetadata) => void
}

export function useAutoRefresh({ sources, onRefreshComplete }: UseAutoRefreshOptions) {
  const [scheduleConfig, setScheduleConfig] = useKV<RefreshScheduleConfig>('refresh-schedule-config', {
    enabled: true,
    schedule: 'manual',
    autoRefreshEnabled: false
  })

  const [refreshMetadata, setRefreshMetadata] = useKV<RefreshMetadata>('data-refresh-metadata', {
    sources: {},
    lastGlobalRefresh: new Date().toISOString()
  })

  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const isRefreshingRef = useRef(false)

  const performScheduledRefresh = useCallback(async () => {
    if (!scheduleConfig?.enabled || !scheduleConfig.autoRefreshEnabled || isRefreshingRef.current) {
      return
    }

    const lastRefresh = refreshMetadata?.lastGlobalRefresh || new Date().toISOString()
    
    if (!shouldRefresh(lastRefresh, scheduleConfig.schedule)) {
      return
    }

    isRefreshingRef.current = true

    try {
      const result = await refreshAllDataSources(sources)
      const now = new Date()
      const nextRefresh = calculateNextRefresh(scheduleConfig.schedule, now)
      
      const updatedMetadata: RefreshMetadata = {
        ...result,
        scheduleConfig: {
          ...scheduleConfig,
          lastScheduledRefresh: now.toISOString(),
          nextScheduledRefresh: nextRefresh?.toISOString()
        }
      }

      setRefreshMetadata(updatedMetadata)

      const successCount = Object.values(result.sources).filter(s => s.status === 'success').length
      const errorCount = Object.values(result.sources).filter(s => s.status === 'error').length

      if (errorCount === 0) {
        toast.success('Scheduled refresh completed', {
          description: `Successfully updated ${successCount} data sources`
        })
      } else {
        toast.warning('Scheduled refresh completed with errors', {
          description: `${successCount} succeeded, ${errorCount} failed`
        })
      }

      onRefreshComplete?.(updatedMetadata)
    } catch (error) {
      toast.error('Scheduled refresh failed', {
        description: 'An unexpected error occurred during automatic refresh'
      })
    } finally {
      isRefreshingRef.current = false
    }
  }, [sources, scheduleConfig, refreshMetadata, setRefreshMetadata, onRefreshComplete])

  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    if (!scheduleConfig?.enabled || !scheduleConfig.autoRefreshEnabled || scheduleConfig.schedule === 'manual' || scheduleConfig.schedule === 'disabled') {
      return
    }

    const checkInterval = scheduleConfig.schedule === 'hourly' ? 60000 : 300000

    intervalRef.current = setInterval(() => {
      performScheduledRefresh()
    }, checkInterval)

    performScheduledRefresh()

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [scheduleConfig, performScheduledRefresh])

  const updateSchedule = useCallback((newSchedule: RefreshSchedule) => {
    const now = new Date()
    const nextRefresh = calculateNextRefresh(newSchedule, now)

    setScheduleConfig((current) => ({
      ...current!,
      schedule: newSchedule,
      nextScheduledRefresh: nextRefresh?.toISOString()
    }))
  }, [setScheduleConfig])

  const toggleAutoRefresh = useCallback((enabled: boolean) => {
    setScheduleConfig((current) => ({
      ...current!,
      autoRefreshEnabled: enabled
    }))
  }, [setScheduleConfig])

  const manualRefresh = useCallback(async () => {
    if (isRefreshingRef.current) {
      return
    }

    isRefreshingRef.current = true

    try {
      const result = await refreshAllDataSources(sources)
      setRefreshMetadata(result)

      const successCount = Object.values(result.sources).filter(s => s.status === 'success').length
      const errorCount = Object.values(result.sources).filter(s => s.status === 'error').length

      if (errorCount === 0) {
        toast.success('All data sources refreshed', {
          description: `Successfully updated ${successCount} data sources`
        })
      } else {
        toast.warning('Refresh completed with errors', {
          description: `${successCount} succeeded, ${errorCount} failed`
        })
      }

      onRefreshComplete?.(result)
      
      return result
    } catch (error) {
      toast.error('Refresh failed', {
        description: 'Failed to refresh data sources'
      })
      throw error
    } finally {
      isRefreshingRef.current = false
    }
  }, [sources, setRefreshMetadata, onRefreshComplete])

  return {
    scheduleConfig,
    refreshMetadata,
    updateSchedule,
    toggleAutoRefresh,
    manualRefresh,
    isRefreshing: isRefreshingRef.current
  }
}
