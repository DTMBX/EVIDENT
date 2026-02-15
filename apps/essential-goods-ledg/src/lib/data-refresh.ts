import type { Source, RefreshSchedule, RefreshScheduleConfig } from './types'

export interface DataRefreshStatus {
  lastRefresh: string
  status: 'idle' | 'refreshing' | 'success' | 'error'
  message?: string
  sourceId: string
}

export interface RefreshMetadata {
  sources: Record<string, DataRefreshStatus>
  lastGlobalRefresh: string
  scheduleConfig?: RefreshScheduleConfig
}

export async function refreshDataSource(sourceId: string): Promise<DataRefreshStatus> {
  return new Promise((resolve) => {
    setTimeout(() => {
      const now = new Date().toISOString()
      const success = Math.random() > 0.1
      
      resolve({
        lastRefresh: now,
        status: success ? 'success' : 'error',
        message: success 
          ? `Successfully retrieved data from ${sourceId}` 
          : `Failed to connect to ${sourceId} API endpoint`,
        sourceId
      })
    }, 1500 + Math.random() * 1000)
  })
}

export async function refreshAllDataSources(sources: Source[]): Promise<RefreshMetadata> {
  const results = await Promise.allSettled(
    sources.map(source => refreshDataSource(source.id))
  )
  
  const sourceStatuses: Record<string, DataRefreshStatus> = {}
  
  results.forEach((result, index) => {
    const sourceId = sources[index].id
    if (result.status === 'fulfilled') {
      sourceStatuses[sourceId] = result.value
    } else {
      sourceStatuses[sourceId] = {
        lastRefresh: new Date().toISOString(),
        status: 'error',
        message: 'Refresh failed unexpectedly',
        sourceId
      }
    }
  })
  
  return {
    sources: sourceStatuses,
    lastGlobalRefresh: new Date().toISOString()
  }
}

export function getTimeSinceRefresh(timestamp: string): string {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  const diffMs = now - then
  
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return new Date(timestamp).toLocaleDateString()
}

export function formatRefreshTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

export function calculateNextRefresh(schedule: RefreshSchedule, fromDate: Date = new Date()): Date | null {
  if (schedule === 'manual' || schedule === 'disabled') {
    return null
  }
  
  const next = new Date(fromDate)
  
  if (schedule === 'hourly') {
    next.setHours(next.getHours() + 1)
    next.setMinutes(0)
    next.setSeconds(0)
    next.setMilliseconds(0)
  } else if (schedule === 'daily') {
    next.setDate(next.getDate() + 1)
    next.setHours(2, 0, 0, 0)
  }
  
  return next
}

export function getScheduleLabel(schedule: RefreshSchedule): string {
  switch (schedule) {
    case 'manual':
      return 'Manual Only'
    case 'hourly':
      return 'Every Hour'
    case 'daily':
      return 'Daily at 2:00 AM'
    case 'disabled':
      return 'Disabled'
    default:
      return 'Unknown'
  }
}

export function shouldRefresh(lastRefresh: string, schedule: RefreshSchedule): boolean {
  if (schedule === 'manual' || schedule === 'disabled') {
    return false
  }
  
  const now = Date.now()
  const last = new Date(lastRefresh).getTime()
  const diffMs = now - last
  
  if (schedule === 'hourly') {
    return diffMs >= 3600000
  } else if (schedule === 'daily') {
    return diffMs >= 86400000
  }
  
  return false
}
