import { useState, useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { 
  MagnifyingGlass, 
  CheckCircle, 
  Circle, 
  ChartLine,
  MapPin,
  Star,
  Package,
  Carrot,
  Flame,
  House,
  Cube,
  Egg
} from '@phosphor-icons/react'
import { EXPANDED_ITEMS, BASKET_TEMPLATES, getItemsByCategory, getItemBySynonym } from '@/lib/expanded-catalog'
import type { Item } from '@/lib/types'
import { useKV } from '@github/spark/hooks'

const CATEGORY_INFO = {
  dairy: { icon: Egg, label: 'Dairy', color: 'text-chart-1' },
  meat: { icon: Package, label: 'Meat', color: 'text-chart-2' },
  proteins: { icon: Package, label: 'Proteins', color: 'text-chart-3' },
  produce: { icon: Carrot, label: 'Produce', color: 'text-chart-4' },
  grains: { icon: Cube, label: 'Grains', color: 'text-chart-5' },
  staples: { icon: Cube, label: 'Staples', color: 'text-primary' },
  household: { icon: House, label: 'Household', color: 'text-accent' },
  fuel: { icon: Flame, label: 'Fuel & Energy', color: 'text-warning' },
  utilities: { icon: Flame, label: 'Utilities', color: 'text-info' },
  inputs: { icon: Carrot, label: 'Ag Inputs', color: 'text-success' },
}

interface ExpandedExploreViewProps {
  selectedItemIds: string[]
  onToggleItem: (itemId: string) => void
  onCompare?: () => void
}

export function ExpandedExploreView({ 
  selectedItemIds, 
  onToggleItem,
  onCompare 
}: ExpandedExploreViewProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [favorites, setFavorites] = useKV<string[]>('favorite-items', [])

  const filteredItems = useMemo(() => {
    let items = [...EXPANDED_ITEMS]

    if (activeCategory !== 'all') {
      if (activeCategory === 'favorites') {
        items = items.filter(item => favorites?.includes(item.id))
      } else {
        items = items.filter(item => item.category === activeCategory)
      }
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      items = items.filter(item =>
        item.name.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query) ||
        item.synonyms?.some(syn => syn.toLowerCase().includes(query)) ||
        item.id.toLowerCase().includes(query)
      )

      const synonymMatch = getItemBySynonym(searchQuery)
      if (synonymMatch && !items.find(i => i.id === synonymMatch.id)) {
        items.unshift(synonymMatch)
      }
    }

    return items
  }, [searchQuery, activeCategory, favorites])

  const categories = useMemo(() => {
    const cats = Array.from(new Set(EXPANDED_ITEMS.map(item => item.category)))
    return cats.sort()
  }, [])

  const toggleFavorite = (itemId: string) => {
    setFavorites((current = []) => {
      if (current.includes(itemId)) {
        return current.filter(id => id !== itemId)
      }
      return [...current, itemId]
    })
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold font-display">Explore Essentials</h1>
        <p className="text-lg text-muted-foreground">
          Browse {EXPANDED_ITEMS.length} tracked essentials across food, household, energy, and inputs
        </p>
      </div>

      <div className="flex flex-col gap-4">
        <div className="relative">
          <MagnifyingGlass 
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" 
            size={20} 
          />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or synonym (e.g., 'hamburger', 'ground beef')..."
            className="pl-10"
          />
        </div>

        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="w-full flex-wrap h-auto">
            <TabsTrigger value="all">All Items</TabsTrigger>
            <TabsTrigger value="favorites">
              <Star className="mr-1" size={16} weight="fill" />
              Favorites {favorites && favorites.length > 0 && `(${favorites.length})`}
            </TabsTrigger>
            {categories.map(cat => {
              const info = CATEGORY_INFO[cat as keyof typeof CATEGORY_INFO]
              const Icon = info?.icon || Package
              return (
                <TabsTrigger key={cat} value={cat}>
                  <Icon className={`mr-1 ${info?.color}`} size={16} />
                  {info?.label || cat}
                </TabsTrigger>
              )
            })}
          </TabsList>
        </Tabs>
      </div>

      {selectedItemIds.length > 0 && (
        <Card className="p-4 bg-primary/5 border-primary/20">
          <div className="flex items-center justify-between gap-4">
            <div>
              <span className="font-semibold">{selectedItemIds.length} item{selectedItemIds.length !== 1 ? 's' : ''} selected</span>
              <span className="text-muted-foreground text-sm ml-2">for comparison</span>
            </div>
            {onCompare && (
              <Button onClick={onCompare}>
                <ChartLine className="mr-2" size={18} />
                Compare Selected
              </Button>
            )}
          </div>
        </Card>
      )}

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-muted-foreground">
            {filteredItems.length} item{filteredItems.length !== 1 ? 's' : ''}
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map(item => {
            const isSelected = selectedItemIds.includes(item.id)
            const isFavorite = favorites?.includes(item.id)
            const categoryInfo = CATEGORY_INFO[item.category as keyof typeof CATEGORY_INFO]
            const CategoryIcon = categoryInfo?.icon || Package

            return (
              <Card 
                key={item.id} 
                className={`p-4 transition-all cursor-pointer ${
                  isSelected ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
                }`}
                onClick={() => onToggleItem(item.id)}
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-3 flex-1">
                      <CategoryIcon 
                        className={`flex-shrink-0 mt-1 ${categoryInfo?.color}`} 
                        size={24} 
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-lg">{item.name}</h4>
                        <p className="text-sm text-muted-foreground">{item.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleFavorite(item.id)
                        }}
                        className="text-muted-foreground hover:text-warning transition-colors"
                      >
                        {isFavorite ? (
                          <Star className="text-warning" size={20} weight="fill" />
                        ) : (
                          <Star size={20} />
                        )}
                      </button>
                      {isSelected ? (
                        <CheckCircle className="text-primary" size={24} />
                      ) : (
                        <Circle className="text-muted-foreground" size={24} />
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap text-xs">
                    <Badge variant="outline" className="font-mono">
                      {item.unitStandard}
                    </Badge>
                    <Badge variant="secondary">
                      {categoryInfo?.label || item.category}
                    </Badge>
                    {item.regionCoverage.length > 0 && (
                      <Badge variant="outline">
                        <MapPin className="mr-1" size={12} />
                        {item.regionCoverage.length} region{item.regionCoverage.length !== 1 ? 's' : ''}
                      </Badge>
                    )}
                  </div>

                  {item.synonyms && item.synonyms.length > 0 && (
                    <div className="text-xs text-muted-foreground">
                      Also: {item.synonyms.slice(0, 2).join(', ')}
                      {item.synonyms.length > 2 && ` +${item.synonyms.length - 2} more`}
                    </div>
                  )}
                </div>
              </Card>
            )
          })}
        </div>

        {filteredItems.length === 0 && (
          <Card className="p-12 text-center">
            <MagnifyingGlass className="mx-auto mb-4 text-muted-foreground" size={48} />
            <h3 className="font-semibold text-lg mb-2">No items found</h3>
            <p className="text-muted-foreground">
              Try adjusting your search or browse by category
            </p>
          </Card>
        )}
      </div>

      <div className="space-y-4">
        <h3 className="text-2xl font-bold font-display">Basket Templates</h3>
        <p className="text-muted-foreground">
          Curated basket presets for common household types
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {BASKET_TEMPLATES.map(template => (
            <Card key={template.id} className="p-4 space-y-3">
              <div>
                <h4 className="font-semibold text-lg">{template.name}</h4>
                <p className="text-sm text-muted-foreground">{template.description}</p>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground">
                  {template.items.length} items
                </div>
                <div className="flex flex-wrap gap-1">
                  {template.items.slice(0, 5).map(({ itemId }) => {
                    const item = EXPANDED_ITEMS.find(i => i.id === itemId)
                    return item ? (
                      <Badge key={itemId} variant="secondary" className="text-xs">
                        {item.name}
                      </Badge>
                    ) : null
                  })}
                  {template.items.length > 5 && (
                    <Badge variant="secondary" className="text-xs">
                      +{template.items.length - 5}
                    </Badge>
                  )}
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => {
                  template.items.forEach(({ itemId }) => {
                    if (!selectedItemIds.includes(itemId)) {
                      onToggleItem(itemId)
                    }
                  })
                }}
              >
                Add All to Comparison
              </Button>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
