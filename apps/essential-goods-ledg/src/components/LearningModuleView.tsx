import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { 
  BookOpen, 
  GraduationCap, 
  TrendUp, 
  CurrencyDollar, 
  ChartLine,
  Newspaper,
  Link as LinkIcon,
  MagnifyingGlass
} from '@phosphor-icons/react'
import { LEARNING_MODULES } from '@/lib/generational-data'
import type { EconomicLearningModule } from '@/lib/types'

export function LearningModuleView() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedModule, setSelectedModule] = useState<EconomicLearningModule | null>(null)

  const categoryIcons = {
    cycles: ChartLine,
    inflation: CurrencyDollar,
    'monetary-policy': TrendUp,
    'supply-shocks': Newspaper,
    media: BookOpen
  }

  const categoryLabels = {
    cycles: 'Business Cycles',
    inflation: 'Inflation',
    'monetary-policy': 'Monetary Policy',
    'supply-shocks': 'Supply Shocks',
    media: 'Media & Perception'
  }

  const filteredModules = LEARNING_MODULES.filter(module => {
    const matchesCategory = selectedCategory === 'all' || module.category === selectedCategory
    const matchesSearch = searchTerm === '' || 
      module.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      module.content.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const categories = ['all', 'cycles', 'inflation', 'monetary-policy', 'supply-shocks', 'media']

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold text-foreground mb-2">
            Economic Literacy Learning Center
          </h1>
          <p className="text-muted-foreground max-w-3xl">
            Build understanding of economic cycles, volatility patterns, and historical context through neutral academic explanations. 
            Foster critical thinking about economic phenomena without assigning blame.
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search learning modules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {categories.map(cat => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(cat)}
            >
              {cat === 'all' ? 'All Topics' : categoryLabels[cat as keyof typeof categoryLabels]}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {selectedModule ? (
            <Card className="p-6">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setSelectedModule(null)}
                className="mb-4"
              >
                ← Back to all modules
              </Button>

              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  {(() => {
                    const Icon = categoryIcons[selectedModule.category]
                    return <Icon className="w-6 h-6 text-primary" />
                  })()}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h2 className="font-display text-2xl font-bold">{selectedModule.title}</h2>
                    <Badge variant="outline">
                      {categoryLabels[selectedModule.category as keyof typeof categoryLabels]}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Reading Level: Grade {selectedModule.readingLevel}</span>
                    <span>•</span>
                    <span>{selectedModule.citations.length} Citations</span>
                  </div>
                </div>
              </div>

              <Separator className="my-6" />

              <div className="prose prose-sm max-w-none mb-6">
                {selectedModule.content.split('\n\n').map((paragraph, i) => (
                  <p key={i} className="mb-4 leading-relaxed">{paragraph}</p>
                ))}
              </div>

              <Separator className="my-6" />

              <div>
                <h3 className="font-display font-semibold mb-3">Sources & Citations</h3>
                <div className="space-y-3">
                  {selectedModule.citations.map((citation, i) => (
                    <div key={i} className="p-3 bg-muted rounded-lg">
                      <div className="flex items-start gap-3">
                        <LinkIcon className="w-4 h-4 text-accent mt-1 flex-shrink-0" />
                        <div className="flex-1">
                          <div className="font-medium text-sm mb-1">{citation.text}</div>
                          <div className="text-xs text-muted-foreground mb-2">{citation.source}</div>
                          <a 
                            href={citation.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-accent hover:underline"
                          >
                            {citation.url}
                          </a>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {selectedModule.relatedTerms.length > 0 && (
                <>
                  <Separator className="my-6" />
                  <div>
                    <h3 className="font-display font-semibold mb-3">Related Terms</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedModule.relatedTerms.map((term, i) => (
                        <Badge key={i} variant="secondary">
                          {term}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredModules.length === 0 ? (
                <Card className="p-12 text-center">
                  <BookOpen className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                  <h3 className="font-display font-semibold mb-2">No modules found</h3>
                  <p className="text-sm text-muted-foreground">
                    Try adjusting your search or filter criteria
                  </p>
                </Card>
              ) : (
                filteredModules.map(module => {
                  const Icon = categoryIcons[module.category]
                  return (
                    <Card 
                      key={module.id} 
                      className="p-6 hover:border-accent/50 transition-colors cursor-pointer"
                      onClick={() => setSelectedModule(module)}
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Icon className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-display font-semibold text-lg">{module.title}</h3>
                            <Badge variant="outline" className="text-xs">
                              {categoryLabels[module.category as keyof typeof categoryLabels]}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                            {module.content.substring(0, 150)}...
                          </p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>Grade {module.readingLevel} Level</span>
                            <span>•</span>
                            <span>{module.citations.length} Citations</span>
                            <span>•</span>
                            <span className="text-accent">Read more →</span>
                          </div>
                        </div>
                      </div>
                    </Card>
                  )
                })
              )}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <GraduationCap className="w-5 h-5 text-primary" />
              <h3 className="font-display font-semibold">Learning Objectives</h3>
            </div>
            <ul className="space-y-3 text-sm">
              <li className="flex gap-2">
                <span className="text-accent">•</span>
                <span>Understand economic cycles as normal market patterns</span>
              </li>
              <li className="flex gap-2">
                <span className="text-accent">•</span>
                <span>Recognize documented causes of volatility</span>
              </li>
              <li className="flex gap-2">
                <span className="text-accent">•</span>
                <span>Distinguish correlation from causation</span>
              </li>
              <li className="flex gap-2">
                <span className="text-accent">•</span>
                <span>Build media literacy for economic news</span>
              </li>
              <li className="flex gap-2">
                <span className="text-accent">•</span>
                <span>Think critically without conspiracy framing</span>
              </li>
            </ul>
          </Card>

          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-accent" />
              <h3 className="font-display font-semibold">Module Statistics</h3>
            </div>
            <div className="space-y-4">
              <div>
                <div className="text-2xl font-mono font-bold text-primary">
                  {LEARNING_MODULES.length}
                </div>
                <div className="text-xs text-muted-foreground">Total Learning Modules</div>
              </div>
              <Separator />
              <div>
                <div className="text-2xl font-mono font-bold text-accent">
                  {LEARNING_MODULES.reduce((sum, m) => sum + m.citations.length, 0)}
                </div>
                <div className="text-xs text-muted-foreground">Academic Citations</div>
              </div>
              <Separator />
              <div>
                <div className="text-lg font-mono font-bold">Grade 10</div>
                <div className="text-xs text-muted-foreground">Average Reading Level</div>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-accent/5 border-accent/20">
            <h3 className="font-display font-semibold mb-3 text-sm">Educational Standards</h3>
            <ul className="space-y-2 text-xs text-muted-foreground">
              <li className="flex gap-2">
                <span>✓</span>
                <span>Neutral academic language</span>
              </li>
              <li className="flex gap-2">
                <span>✓</span>
                <span>Credible source citations</span>
              </li>
              <li className="flex gap-2">
                <span>✓</span>
                <span>10th grade reading level</span>
              </li>
              <li className="flex gap-2">
                <span>✓</span>
                <span>No political framing</span>
              </li>
              <li className="flex gap-2">
                <span>✓</span>
                <span>Systematic explanations</span>
              </li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  )
}
