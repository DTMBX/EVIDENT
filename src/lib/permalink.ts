import type { AnalyticsConfig } from './types'

export interface PermalinkData {
  config: AnalyticsConfig
  created: string
  version: string
}

const PERMALINK_VERSION = '1.0'

export function encodePermalink(config: AnalyticsConfig): string {
  const data: PermalinkData = {
    config,
    created: new Date().toISOString(),
    version: PERMALINK_VERSION
  }
  
  const json = JSON.stringify(data)
  const base64 = btoa(encodeURIComponent(json))
  
  return base64
}

export function decodePermalink(encoded: string): AnalyticsConfig | null {
  try {
    const json = decodeURIComponent(atob(encoded))
    const data: PermalinkData = JSON.parse(json)
    
    if (!data.config || !data.version) {
      return null
    }
    
    return data.config
  } catch (error) {
    console.error('Failed to decode permalink:', error)
    return null
  }
}

export function generatePermalinkURL(config: AnalyticsConfig): string {
  const encoded = encodePermalink(config)
  const url = new URL(window.location.href)
  url.searchParams.set('config', encoded)
  url.hash = '#analytics'
  
  return url.toString()
}

export function getPermalinkFromURL(): AnalyticsConfig | null {
  const params = new URLSearchParams(window.location.search)
  const encoded = params.get('config')
  
  if (!encoded) {
    return null
  }
  
  return decodePermalink(encoded)
}

export function generatePermalinkHash(config: AnalyticsConfig): string {
  const json = JSON.stringify(config)
  let hash = 0
  
  for (let i = 0; i < json.length; i++) {
    const char = json.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  
  return Math.abs(hash).toString(16).padStart(8, '0')
}
