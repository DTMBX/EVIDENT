import type { RawPricePoint, UnitStandard } from './types'

export interface APIClientConfig {
  baseUrl: string
  retryAttempts: number
  retryDelayMs: number
  timeoutMs: number
}

export interface BLSSeriesRequest {
  seriesId: string
  startYear: string
  endYear: string
  region?: string
}

export interface EIASeriesRequest {
  seriesId: string
  startDate: string
  endDate: string
}

export interface USDAQuickStatsRequest {
  commodity: string
  dataItem: string
  domain: string
  year?: string
  beginDate?: string
  endDate?: string
  state?: string
}

class RateLimiter {
  private queue: Array<() => Promise<void>> = []
  private processing = false
  private lastRequestTime = 0

  constructor(
    private requestsPerMinute: number,
    private requestsPerHour: number
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn()
          resolve(result)
        } catch (error) {
          reject(error)
        }
      })
      this.processQueue()
    })
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return

    this.processing = true
    const minDelay = 60000 / this.requestsPerMinute

    while (this.queue.length > 0) {
      const now = Date.now()
      const timeSinceLastRequest = now - this.lastRequestTime

      if (timeSinceLastRequest < minDelay) {
        await new Promise(resolve => setTimeout(resolve, minDelay - timeSinceLastRequest))
      }

      const task = this.queue.shift()
      if (task) {
        this.lastRequestTime = Date.now()
        await task()
      }
    }

    this.processing = false
  }
}

const rateLimiters = new Map<string, RateLimiter>()

function getRateLimiter(connectorId: string, requestsPerMinute: number, requestsPerHour: number): RateLimiter {
  if (!rateLimiters.has(connectorId)) {
    rateLimiters.set(connectorId, new RateLimiter(requestsPerMinute, requestsPerHour))
  }
  return rateLimiters.get(connectorId)!
}

export class BLSAPIClient {
  private config: APIClientConfig = {
    baseUrl: 'https://api.bls.gov/publicAPI/v2',
    retryAttempts: 3,
    retryDelayMs: 2000,
    timeoutMs: 30000,
  }

  private rateLimiter = getRateLimiter('bls', 25, 500)

  async fetchSeries(request: BLSSeriesRequest): Promise<RawPricePoint[]> {
    return this.rateLimiter.execute(async () => {
      const startYear = parseInt(request.startYear)
      const endYear = parseInt(request.endYear)
      const points: RawPricePoint[] = []

      for (let year = startYear; year <= endYear; year += 10) {
        const batchEndYear = Math.min(year + 9, endYear)
        const batchPoints = await this.fetchSeriesBatch(
          request.seriesId,
          year.toString(),
          batchEndYear.toString()
        )
        points.push(...batchPoints)
      }

      return points
    })
  }

  private async fetchSeriesBatch(
    seriesId: string,
    startYear: string,
    endYear: string
  ): Promise<RawPricePoint[]> {
    const url = `${this.config.baseUrl}/timeseries/data/`
    const body = {
      seriesid: [seriesId],
      startyear: startYear,
      endyear: endYear,
      registrationkey: 'PUBLIC',
    }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs)

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`BLS API error: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()

      if (data.status !== 'REQUEST_SUCCEEDED') {
        throw new Error(`BLS API request failed: ${data.message || 'Unknown error'}`)
      }

      if (!data.Results || !data.Results.series || data.Results.series.length === 0) {
        return []
      }

      const series = data.Results.series[0]
      const points: RawPricePoint[] = []

      for (const dataPoint of series.data || []) {
        const year = dataPoint.year
        const period = dataPoint.period

        let date: string
        if (period.startsWith('M')) {
          const month = period.substring(1).padStart(2, '0')
          date = `${year}-${month}-01`
        } else if (period === 'A01') {
          date = `${year}-01-01`
        } else {
          continue
        }

        const value = parseFloat(dataPoint.value)
        if (isNaN(value)) continue

        points.push({
          id: `${seriesId}-${date}-raw`,
          itemId: this.mapBLSSeriesIdToItem(seriesId),
          date,
          region: 'US-National',
          value,
          unit: this.getUnitForSeries(seriesId),
          sourceId: 'bls-cpi',
          retrievalTimestamp: new Date().toISOString(),
          sourceUrl: `https://data.bls.gov/timeseries/${seriesId}`,
          checksumHash: this.generateChecksum(seriesId, date, value),
        })
      }

      return points.sort((a, b) => a.date.localeCompare(b.date))
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('BLS API request timeout')
      }
      throw error
    }
  }

  private mapBLSSeriesIdToItem(seriesId: string): string {
    if (seriesId.includes('CPI')) return 'cpi-all-items'
    if (seriesId.includes('WAGE')) return 'wage-median'
    return 'unknown'
  }

  private getUnitForSeries(seriesId: string): UnitStandard {
    if (seriesId.includes('CPI')) return 'count'
    if (seriesId.includes('WAGE')) return 'count'
    return 'count'
  }

  private generateChecksum(seriesId: string, date: string, value: number): string {
    const data = `${seriesId}-${date}-${value}`
    let hash = 0
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash).toString(16)
  }
}

export class EIAAPIClient {
  private config: APIClientConfig = {
    baseUrl: 'https://api.eia.gov/v2',
    retryAttempts: 3,
    retryDelayMs: 1500,
    timeoutMs: 30000,
  }

  private rateLimiter = getRateLimiter('eia', 100, 5000)

  async fetchSeries(request: EIASeriesRequest): Promise<RawPricePoint[]> {
    return this.rateLimiter.execute(async () => {
      return this.fetchSeriesData(request.seriesId, request.startDate, request.endDate)
    })
  }

  private async fetchSeriesData(
    seriesId: string,
    startDate: string,
    endDate: string
  ): Promise<RawPricePoint[]> {
    const route = this.getRouteForSeries(seriesId)
    const url = `${this.config.baseUrl}${route}/data/`
    
    const params = new URLSearchParams({
      frequency: 'monthly',
      'data[0]': 'value',
      start: startDate.substring(0, 7),
      end: endDate.substring(0, 7),
      sort: 'date',
      api_key: 'DEMO_KEY',
    })

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs)

      const response = await fetch(`${url}?${params}`, {
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`EIA API error: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()

      if (!data.response || !data.response.data) {
        return []
      }

      const points: RawPricePoint[] = []

      for (const dataPoint of data.response.data) {
        const date = this.parseDateFromEIA(dataPoint.period)
        const value = parseFloat(dataPoint.value)
        
        if (isNaN(value) || !date) continue

        points.push({
          id: `${seriesId}-${date}-raw`,
          itemId: this.mapEIASeriesIdToItem(seriesId),
          date,
          region: this.getRegionFromSeries(seriesId),
          value,
          unit: this.getUnitForSeries(seriesId),
          sourceId: this.getSourceIdForSeries(seriesId),
          retrievalTimestamp: new Date().toISOString(),
          sourceUrl: `https://www.eia.gov/dnav/pet/hist/${seriesId}.htm`,
          checksumHash: this.generateChecksum(seriesId, date, value),
        })
      }

      return points.sort((a, b) => a.date.localeCompare(b.date))
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('EIA API request timeout')
      }
      throw error
    }
  }

  private getRouteForSeries(seriesId: string): string {
    if (seriesId.includes('PET')) return '/petroleum'
    if (seriesId.includes('NG')) return '/natural-gas'
    if (seriesId.includes('ELEC')) return '/electricity'
    return '/petroleum'
  }

  private parseDateFromEIA(period: string): string | null {
    if (period.match(/^\d{4}-\d{2}$/)) {
      return `${period}-01`
    }
    return null
  }

  private mapEIASeriesIdToItem(seriesId: string): string {
    if (seriesId.includes('GASOLINE')) return 'gasoline-gallon'
    if (seriesId.includes('DIESEL')) return 'diesel-gallon'
    if (seriesId.includes('PROPANE')) return 'propane-gallon'
    if (seriesId.includes('HEAT')) return 'heating-oil-gallon'
    if (seriesId.includes('NG')) return 'natural-gas-therm'
    if (seriesId.includes('ELEC')) return 'electricity-kWh'
    return 'unknown'
  }

  private getRegionFromSeries(seriesId: string): string {
    return 'US-National'
  }

  private getSourceIdForSeries(seriesId: string): string {
    if (seriesId.includes('PET')) return 'eia-petroleum'
    if (seriesId.includes('NG')) return 'eia-natural-gas'
    if (seriesId.includes('ELEC')) return 'eia-electricity'
    return 'eia-petroleum'
  }

  private getUnitForSeries(seriesId: string): UnitStandard {
    if (seriesId.includes('GALLON') || seriesId.includes('GAL')) return 'gallon'
    if (seriesId.includes('THERM')) return 'therm'
    if (seriesId.includes('KWH')) return 'kWh'
    return 'gallon'
  }

  private generateChecksum(seriesId: string, date: string, value: number): string {
    const data = `${seriesId}-${date}-${value}`
    let hash = 0
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash).toString(16)
  }
}

export class USDAAPIClient {
  private config: APIClientConfig = {
    baseUrl: 'https://quickstats.nass.usda.gov/api',
    retryAttempts: 3,
    retryDelayMs: 1000,
    timeoutMs: 30000,
  }

  private rateLimiter = getRateLimiter('usda', 60, 1000)

  async fetchQuickStats(request: USDAQuickStatsRequest): Promise<RawPricePoint[]> {
    return this.rateLimiter.execute(async () => {
      return this.fetchQuickStatsData(request)
    })
  }

  private async fetchQuickStatsData(request: USDAQuickStatsRequest): Promise<RawPricePoint[]> {
    const url = `${this.config.baseUrl}/api_GET/`
    
    const params = new URLSearchParams({
      key: 'DEMO_KEY',
      commodity_desc: request.commodity,
      statisticcat_desc: 'PRICE RECEIVED',
      agg_level_desc: 'NATIONAL',
      format: 'JSON',
    })

    if (request.year) params.append('year', request.year)
    if (request.beginDate) params.append('begin_date', request.beginDate)
    if (request.endDate) params.append('end_date', request.endDate)

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs)

      const response = await fetch(`${url}?${params}`, {
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`USDA API error: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()

      if (!data.data || !Array.isArray(data.data)) {
        return []
      }

      const points: RawPricePoint[] = []

      for (const dataPoint of data.data) {
        const year = dataPoint.year
        const period = dataPoint.reference_period_desc

        let date: string
        if (period && period.includes('MONTH')) {
          const monthMatch = period.match(/(\w+)/)
          if (monthMatch) {
            const monthName = monthMatch[1]
            const monthNum = this.monthNameToNumber(monthName)
            date = `${year}-${monthNum.toString().padStart(2, '0')}-01`
          } else {
            date = `${year}-01-01`
          }
        } else {
          date = `${year}-01-01`
        }

        const value = parseFloat(dataPoint.Value)
        if (isNaN(value)) continue

        points.push({
          id: `usda-${request.commodity}-${date}-raw`,
          itemId: this.mapCommodityToItem(request.commodity),
          date,
          region: 'US-National',
          value,
          unit: this.getUnitForCommodity(request.commodity),
          sourceId: 'usda-nass',
          retrievalTimestamp: new Date().toISOString(),
          sourceUrl: `https://quickstats.nass.usda.gov/`,
          checksumHash: this.generateChecksum(request.commodity, date, value),
        })
      }

      return points.sort((a, b) => a.date.localeCompare(b.date))
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('USDA API request timeout')
      }
      throw error
    }
  }

  private monthNameToNumber(monthName: string): number {
    const months: Record<string, number> = {
      'JAN': 1, 'JANUARY': 1,
      'FEB': 2, 'FEBRUARY': 2,
      'MAR': 3, 'MARCH': 3,
      'APR': 4, 'APRIL': 4,
      'MAY': 5,
      'JUN': 6, 'JUNE': 6,
      'JUL': 7, 'JULY': 7,
      'AUG': 8, 'AUGUST': 8,
      'SEP': 9, 'SEPT': 9, 'SEPTEMBER': 9,
      'OCT': 10, 'OCTOBER': 10,
      'NOV': 11, 'NOVEMBER': 11,
      'DEC': 12, 'DECEMBER': 12,
    }
    return months[monthName.toUpperCase()] || 1
  }

  private mapCommodityToItem(commodity: string): string {
    const commodityMap: Record<string, string> = {
      'MILK': 'milk-gallon',
      'EGGS': 'eggs-dozen',
      'BUTTER': 'butter-lb',
      'CHEESE': 'cheese-lb',
      'CATTLE': 'ground-beef-lb',
      'HOGS': 'pork-chops-lb',
      'BROILERS': 'chicken-breast-lb',
      'CORN': 'flour-lb',
      'WHEAT': 'bread-loaf',
      'SOYBEANS': 'beans-dry-lb',
      'POTATOES': 'potatoes-lb',
      'APPLES': 'apples-lb',
      'TOMATOES': 'tomatoes-lb',
    }
    return commodityMap[commodity.toUpperCase()] || 'unknown'
  }

  private getUnitForCommodity(commodity: string): UnitStandard {
    const unitMap: Record<string, UnitStandard> = {
      'MILK': 'gallon',
      'EGGS': 'dozen',
      'BUTTER': 'lb',
      'CHEESE': 'lb',
      'CATTLE': 'lb',
      'HOGS': 'lb',
      'BROILERS': 'lb',
      'CORN': 'bushel',
      'WHEAT': 'bushel',
      'SOYBEANS': 'bushel',
      'POTATOES': 'lb',
      'APPLES': 'lb',
      'TOMATOES': 'lb',
    }
    return unitMap[commodity.toUpperCase()] || 'lb'
  }

  private generateChecksum(commodity: string, date: string, value: number): string {
    const data = `${commodity}-${date}-${value}`
    let hash = 0
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash).toString(16)
  }
}

export const blsClient = new BLSAPIClient()
export const eiaClient = new EIAAPIClient()
export const usdaClient = new USDAAPIClient()
