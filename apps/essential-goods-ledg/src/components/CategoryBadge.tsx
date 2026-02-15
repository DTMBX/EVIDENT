import { Badge } from '@/components/ui/badge'
import type { ItemCategory } from '@/lib/types'

interface CategoryBadgeProps {
  category: ItemCategory
}

const CATEGORY_CONFIG = {
  dairy: { label: 'Dairy', color: 'bg-[var(--chart-1)] text-white' },
  meat: { label: 'Meat', color: 'bg-[var(--chart-2)] text-white' },
  fuel: { label: 'Fuel', color: 'bg-[var(--chart-3)] text-white' },
  household: { label: 'Household', color: 'bg-[var(--chart-4)] text-white' }
} as const

export function CategoryBadge({ category }: CategoryBadgeProps) {
  const config = CATEGORY_CONFIG[category]
  
  return (
    <Badge className={config.color} variant="secondary">
      {config.label}
    </Badge>
  )
}
