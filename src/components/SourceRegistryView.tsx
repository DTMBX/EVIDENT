import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Database, 
  Link as LinkIcon, 
  CheckCircle, 
  Warning,
  XCircle,
  Clock,
  MapPin,
  FileText,
  Shield
} from '@phosphor-icons/react'
import { EXPANDED_SOURCES, EXPANDED_ITEMS } from '@/lib/expanded-catalog'
import { DATA_CONNECTORS } from '@/lib/data-connectors'

export function SourceRegistryView() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold font-display">Source Registry</h1>
        <p className="text-lg text-muted-foreground">
          Complete registry of all data sources, providers, licensing terms, and coverage metadata
        </p>
      </div>

      <Card className="p-6 bg-accent/10 border-accent/20">
        <div className="flex items-start gap-3">
          <Shield className="text-accent flex-shrink-0 mt-1" size={24} />
          <div className="space-y-1">
            <h3 className="font-semibold text-accent-foreground">Data Integrity Guarantee</h3>
            <p className="text-sm text-muted-foreground">
              Every data point in Chronos traces back to a verified public source with clear licensing.
              This registry is the single source of truth for what data powers this platform.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid gap-6">
        {EXPANDED_SOURCES.map(source => {
          const connector = DATA_CONNECTORS.find(c => c.sourceId === source.id)
          const coveredItems = EXPANDED_ITEMS.filter(item => 
            item.sourceSeriesIds.includes(source.id)
          )
          const totalRegions = Object.keys(source.coverageMap).length
          
          return (
            <Card key={source.id} className="p-6 space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <Database className="text-primary flex-shrink-0 mt-1" size={32} />
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-xl font-bold font-display">{source.name}</h3>
                      {source.isOfficial && (
                        <Badge variant="default" className="bg-primary/20 text-primary border-primary/30">
                          <CheckCircle className="mr-1" size={14} />
                          Official
                        </Badge>
                      )}
                      <Badge 
                        variant={source.reliabilityTier === 'tier-1' ? 'default' : 'secondary'}
                        className={source.reliabilityTier === 'tier-1' ? 'bg-success/20 text-success border-success/30' : ''}
                      >
                        {source.reliabilityTier.toUpperCase()}
                      </Badge>
                      <Badge 
                        variant={source.status === 'active' ? 'default' : 'secondary'}
                        className={source.status === 'active' ? 'bg-success/20 text-success border-success/30' : 'bg-warning/20 text-warning border-warning/30'}
                      >
                        {source.status === 'active' ? (
                          <><CheckCircle className="mr-1" size={14} />Active</>
                        ) : source.status === 'maintenance' ? (
                          <><Warning className="mr-1" size={14} />Maintenance</>
                        ) : (
                          <><XCircle className="mr-1" size={14} />Deprecated</>
                        )}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground">{source.provider}</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <FileText size={16} />
                    <span className="font-semibold">License</span>
                  </div>
                  <p className="text-foreground">{source.license}</p>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Shield size={16} />
                    <span className="font-semibold">Terms</span>
                  </div>
                  <p className="text-foreground">{source.terms}</p>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Clock size={16} />
                    <span className="font-semibold">Refresh Schedule</span>
                  </div>
                  <p className="text-foreground capitalize">{source.refreshSchedule}</p>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <MapPin size={16} />
                    <span className="font-semibold">Coverage</span>
                  </div>
                  <p className="text-foreground">{totalRegions} region{totalRegions !== 1 ? 's' : ''}</p>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold text-sm text-muted-foreground">Series Identifiers</h4>
                <div className="flex flex-wrap gap-2">
                  {source.seriesIdentifiers.map(id => (
                    <Badge key={id} variant="outline" className="font-mono text-xs">
                      {id}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold text-sm text-muted-foreground">Covered Items ({coveredItems.length})</h4>
                <div className="flex flex-wrap gap-2">
                  {coveredItems.slice(0, 10).map(item => (
                    <Badge key={item.id} variant="secondary">
                      {item.name}
                    </Badge>
                  ))}
                  {coveredItems.length > 10 && (
                    <Badge variant="secondary">
                      +{coveredItems.length - 10} more
                    </Badge>
                  )}
                </div>
              </div>

              {connector && (
                <div className="space-y-2 pt-2 border-t border-border">
                  <h4 className="font-semibold text-sm text-muted-foreground">Connector Status</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="text-muted-foreground">State: </span>
                      <span className={connector.enabled ? 'text-success' : 'text-muted-foreground'}>
                        {connector.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Rate Limit: </span>
                      <span className="text-foreground">
                        {connector.rateLimit.requestsPerMinute}/min, {connector.rateLimit.requestsPerHour}/hr
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Max Retries: </span>
                      <span className="text-foreground">{connector.retryConfig.maxRetries}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3 pt-2">
                <Button variant="outline" size="sm" asChild>
                  <a href={source.url} target="_blank" rel="noopener noreferrer">
                    <LinkIcon className="mr-2" size={16} />
                    Visit Source
                  </a>
                </Button>
                {source.lastSuccessfulFetch && (
                  <span className="text-xs text-muted-foreground">
                    Last fetched: {new Date(source.lastSuccessfulFetch).toLocaleString()}
                  </span>
                )}
              </div>

              {source.lastError && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                  <p className="text-sm text-destructive font-semibold">Last Error:</p>
                  <p className="text-xs text-destructive/80 mt-1">{source.lastError}</p>
                </div>
              )}
            </Card>
          )
        })}
      </div>

      <Card className="p-6 bg-muted/50">
        <h3 className="font-bold text-lg mb-3">Coverage Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-3xl font-bold font-mono text-primary">{EXPANDED_SOURCES.length}</div>
            <div className="text-sm text-muted-foreground">Total Sources</div>
          </div>
          <div>
            <div className="text-3xl font-bold font-mono text-primary">
              {EXPANDED_SOURCES.filter(s => s.isOfficial).length}
            </div>
            <div className="text-sm text-muted-foreground">Official Sources</div>
          </div>
          <div>
            <div className="text-3xl font-bold font-mono text-primary">{EXPANDED_ITEMS.length}</div>
            <div className="text-sm text-muted-foreground">Total Items</div>
          </div>
          <div>
            <div className="text-3xl font-bold font-mono text-primary">
              {DATA_CONNECTORS.filter(c => c.enabled).length}/{DATA_CONNECTORS.length}
            </div>
            <div className="text-sm text-muted-foreground">Active Connectors</div>
          </div>
        </div>
      </Card>
    </div>
  )
}
