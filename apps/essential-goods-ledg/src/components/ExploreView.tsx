import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CategoryBadge } from '@/components/CategoryBadge'
import { MagnifyingGlass, Plus, Check } from '@phosphor-icons/react'
import { ITEMS, getLatestPrice, calculateHoursOfWork } from '@/lib/data'
import type { ItemCategory } from '@/lib/types'

interface ExploreViewProps {
  selectedItemIds: string[]
  onToggleItem: (itemId: string) => void
  hourlyWage: number
}

export function ExploreView({ selectedItemIds, onToggleItem, hourlyWage }: ExploreViewProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<ItemCategory | 'all'>('all')

  const categories: Array<ItemCategory | 'all'> = ['all', 'dairy', 'meat', 'fuel', 'household']

  const filteredItems = ITEMS.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold mb-1 sm:mb-2">Explore Items</h1>
        <p className="text-sm sm:text-base text-muted-foreground">
          Search and select items to add to your comparison
        </p>
      </div>

      <div className="space-y-3 sm:space-y-4">
        <div className="relative">
          <MagnifyingGlass
            size={18}
            className="absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            placeholder="Search items..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 sm:pl-10 text-sm sm:text-base h-10 sm:h-11"
          />
        </div>

        <div className="flex gap-1.5 sm:gap-2 flex-wrap">
          {categories.map(cat => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(cat)}
              className="text-xs sm:text-sm touch-manipulation"
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Button>
          ))}
        </div>

        {selectedItemIds.length > 0 && (
          <Card className="p-3 sm:p-4 bg-accent/10 border-accent">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm sm:text-base">
                  {selectedItemIds.length} item{selectedItemIds.length !== 1 ? 's' : ''} selected
                </p>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Ready for comparison
                </p>
              </div>
            </div>
          </Card>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
        {filteredItems.map(item => {
          const latest = getLatestPrice(item.id)
          const hoursOfWork = latest 
            ? calculateHoursOfWork(latest.nominalPrice, hourlyWage)
            : 0
          const isSelected = selectedItemIds.includes(item.id)

          return (
            <Card 
              key={item.id}
              className={`p-3 sm:p-4 transition-all hover:shadow-md touch-manipulation ${
                isSelected ? 'ring-2 ring-accent' : ''
              }`}
            >
              <div className="space-y-2 sm:space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold mb-1 sm:mb-2 text-sm sm:text-base">{item.name}</h3>
                    <p className="text-xs sm:text-sm text-muted-foreground mb-1.5 sm:mb-2 line-clamp-2">
                      {item.description}
                    </p>
                    <CategoryBadge category={item.category} />
                  </div>
                </div>

                {latest && (
                  <div className="space-y-1 pt-2 border-t">
                    <div className="flex items-baseline gap-1.5 sm:gap-2">
                      <span className="text-lg sm:text-xl font-bold font-mono">
                        ${latest.nominalPrice.toFixed(2)}
                      </span>
                      <span className="text-xs sm:text-sm text-muted-foreground">
                        /{item.unitStandard}
                      </span>
                    </div>
                    <div className="text-xs sm:text-sm text-muted-foreground font-mono">
                      {hoursOfWork.toFixed(2)} hours of work
                    </div>
                  </div>
                )}

                <Button
                  variant={isSelected ? 'secondary' : 'default'}
                  size="sm"
                  className="w-full text-xs sm:text-sm touch-manipulation"
                  onClick={() => onToggleItem(item.id)}
                >
                  {isSelected ? (
                    <>
                      <Check size={16} className="mr-1.5 sm:mr-2" />
                      Selected
                    </>
                  ) : (
                    <>
                      <Plus size={16} className="mr-1.5 sm:mr-2" />
                      Add to Compare
                    </>
                  )}
                </Button>
              </div>
            </Card>
          )
        })}
      </div>

      {filteredItems.length === 0 && (
        <Card className="p-12 text-center">
          <MagnifyingGlass size={48} className="mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No items found</h3>
          <p className="text-muted-foreground">
            Try adjusting your search or category filter
          </p>
        </Card>
      )}
    </div>
  )
}
