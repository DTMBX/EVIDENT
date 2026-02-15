import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { ShareNetwork, Copy, Check, Info } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { generatePermalinkURL, generatePermalinkHash } from '@/lib/permalink'
import type { AnalyticsConfig } from '@/lib/types'

interface SharePermalinkProps {
  config: AnalyticsConfig
}

export function SharePermalink({ config }: SharePermalinkProps) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  
  const permalinkURL = generatePermalinkURL(config)
  const configHash = generatePermalinkHash(config)
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(permalinkURL)
      setCopied(true)
      toast.success('Permalink copied to clipboard')
      
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast.error('Failed to copy to clipboard')
    }
  }
  
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <ShareNetwork size={16} />
          Share Configuration
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl">Share Analytics Configuration</DialogTitle>
          <DialogDescription>
            Generate a permanent link to this exact analytics configuration for reproducible analysis
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6 mt-4">
          <div className="space-y-2">
            <Label htmlFor="permalink-url">Permalink URL</Label>
            <div className="flex gap-2">
              <Input
                id="permalink-url"
                value={permalinkURL}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                onClick={handleCopy}
                variant="outline"
                size="icon"
                className="shrink-0"
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              This URL contains all configuration parameters and will load this exact analysis when accessed
            </p>
          </div>
          
          <Card className="p-4 bg-muted/50">
            <div className="flex gap-2 items-start mb-3">
              <Info size={16} className="mt-0.5 text-accent shrink-0" />
              <div>
                <h4 className="font-medium text-sm mb-1">Configuration Hash</h4>
                <p className="text-xs text-muted-foreground mb-2">
                  Use this hash to verify configuration integrity in published work
                </p>
                <code className="text-xs font-mono bg-background px-2 py-1 rounded">
                  {configHash}
                </code>
              </div>
            </div>
          </Card>
          
          <div className="space-y-3">
            <h4 className="font-medium text-sm">Current Configuration</h4>
            
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-muted-foreground">Region:</span>
                <span className="ml-2 font-medium">{config.region}</span>
              </div>
              
              <div>
                <span className="text-muted-foreground">Wage Type:</span>
                <span className="ml-2 font-medium capitalize">{config.wageType}</span>
              </div>
              
              <div>
                <span className="text-muted-foreground">Metric Mode:</span>
                <span className="ml-2 font-medium">
                  {config.metricMode === 'hours-of-work' ? 'Hours of Work' : 
                   config.metricMode === 'real' ? 'Real ($, CPI-adj)' : 'Nominal ($)'}
                </span>
              </div>
              
              <div>
                <span className="text-muted-foreground">Date Range:</span>
                <span className="ml-2 font-medium">
                  {formatDate(config.dateRange.start)} - {formatDate(config.dateRange.end)}
                </span>
              </div>
              
              <div>
                <span className="text-muted-foreground">Base Date:</span>
                <span className="ml-2 font-medium">{formatDate(config.baseDate)}</span>
              </div>
              
              <div>
                <span className="text-muted-foreground">Basket Items:</span>
                <span className="ml-2 font-medium">{config.basketItemIds.length} items</span>
              </div>
              
              <div>
                <span className="text-muted-foreground">Verdict Threshold:</span>
                <span className="ml-2 font-medium">{config.verdictThreshold.toFixed(2)}</span>
              </div>
              
              <div>
                <span className="text-muted-foreground">Event Window:</span>
                <span className="ml-2 font-medium">{config.eventWindowMonths} months</span>
              </div>
            </div>
          </div>
          
          <Card className="p-4 bg-accent/5 border-accent/20">
            <h4 className="font-medium text-sm mb-2">Best Practices for Sharing</h4>
            <ul className="text-xs space-y-1 text-muted-foreground">
              <li>• Include the configuration hash in footnotes or data tables</li>
              <li>• Document the permalink creation date for audit trails</li>
              <li>• Verify the link loads correctly before publishing</li>
              <li>• Consider archiving the full URL in your research documentation</li>
            </ul>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  )
}
