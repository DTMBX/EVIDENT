import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface ConfidenceBadgeProps {
  confidence: 'high' | 'medium' | 'low'
}

const CONFIDENCE_CONFIG = {
  high: {
    label: 'High Confidence',
    color: 'bg-[var(--chart-3)] text-white',
    description: 'Data from primary government sources with complete coverage'
  },
  medium: {
    label: 'Medium Confidence',
    color: 'bg-[var(--chart-2)] text-white',
    description: 'Data from secondary sources or with partial coverage'
  },
  low: {
    label: 'Low Confidence',
    color: 'bg-[var(--decrease)] text-white',
    description: 'Limited data availability or extrapolated values'
  }
} as const

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const config = CONFIDENCE_CONFIG[confidence]
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge className={config.color} variant="secondary">
            {config.label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs max-w-xs">{config.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
