import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { Logo } from '@/components/Logo'
import {
  HomeIcon,
  ExploreIcon,
  CompareIcon,
  AnalyticsIcon,
  GenerationsIcon,
  VolatilityIcon,
  EducationIcon,
  MethodologyIcon,
  DataSourceIcon,
  SettingsIcon,
  MonitoringIcon,
  RemediationIcon,
  TestIcon
} from '@/components/icons'

interface MobileNavProps {
  isOpen: boolean
  onClose: () => void
  activeTab: string
  onTabChange: (tab: string) => void
  selectedItemsCount: number
}

const navItems = [
  { id: 'home', label: 'Home', icon: HomeIcon, description: 'Dashboard overview' },
  { id: 'explore', label: 'Explore', icon: ExploreIcon, description: 'Browse essential goods' },
  { id: 'expanded-catalog', label: 'Full Catalog', icon: ExploreIcon, description: '40+ tracked essentials', highlight: true },
  { id: 'compare', label: 'Compare', icon: CompareIcon, description: 'Chart builder', badge: true },
  { id: 'analytics', label: 'Analytics', icon: AnalyticsIcon, description: 'Wage vs essentials' },
  { id: 'generations', label: 'Generations', icon: GenerationsIcon, description: 'Cross-generational timeline', highlight: true },
  { id: 'volatility', label: 'Volatility', icon: VolatilityIcon, description: 'Stability explorer', highlight: true },
  { id: 'learn', label: 'Learn', icon: EducationIcon, description: 'Economic literacy', highlight: true },
  { id: 'methodology', label: 'Methodology', icon: MethodologyIcon, description: 'Formulas & sources' },
  { id: 'sources', label: 'Sources', icon: DataSourceIcon, description: 'API data refresh' },
  { id: 'registry', label: 'Source Registry', icon: DataSourceIcon, description: 'Data provenance & quality', highlight: true },
  { id: 'monitoring', label: 'Data Quality', icon: MonitoringIcon, description: 'Real-time API monitoring', highlight: true },
  { id: 'remediation', label: 'Auto-Remediation', icon: RemediationIcon, description: 'Automated connector recovery', highlight: true },
  { id: 'test-suite', label: 'Test Suite', icon: TestIcon, description: 'Connector failure testing', highlight: true },
  { id: 'settings', label: 'Settings', icon: SettingsIcon, description: 'Configure wage' },
]

export function MobileNav({ isOpen, onClose, activeTab, onTabChange, selectedItemsCount }: MobileNavProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  const handleNavClick = (tabId: string) => {
    onTabChange(tabId)
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-foreground/60 backdrop-blur-sm z-50"
            onClick={onClose}
          />
          
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed left-0 top-0 bottom-0 w-72 sm:w-80 max-w-[85vw] bg-card border-r border-border z-50 flex flex-col shadow-2xl"
          >
            <div className="flex items-center justify-between p-4 sm:p-6 border-b border-border">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 text-primary">
                  <Logo size={window.innerWidth < 640 ? 32 : 40} />
                </div>
                <div>
                  <h2 className="font-display font-bold text-sm sm:text-base leading-tight">
                    Chronos
                  </h2>
                  <p className="text-[10px] sm:text-xs text-muted-foreground leading-tight">
                    Economic Insights
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="h-9 w-9 sm:h-10 sm:w-10 min-h-[44px] min-w-[44px] rounded-lg hover:bg-muted touch-manipulation"
              >
                <X size={20} weight="bold" />
              </Button>
            </div>

            <nav className="flex-1 overflow-y-auto p-3 sm:p-4">
              <ul className="space-y-0.5 sm:space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = activeTab === item.id
                  const showBadge = item.badge && selectedItemsCount > 0
                  
                  return (
                    <li key={item.id}>
                      <button
                        onClick={() => handleNavClick(item.id)}
                        className={cn(
                          'w-full flex items-center gap-3 sm:gap-4 px-3 py-2.5 sm:px-4 sm:py-3.5 rounded-lg transition-all duration-200 group relative overflow-hidden touch-manipulation',
                          isActive && item.highlight
                            ? 'bg-accent text-accent-foreground shadow-sm'
                            : isActive
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'text-foreground hover:bg-muted hover:text-foreground'
                        )}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="mobile-active-bg"
                            className={cn(
                              "absolute inset-0 rounded-lg",
                              item.highlight ? "bg-accent" : "bg-primary"
                            )}
                            initial={false}
                            transition={{ type: 'spring', damping: 30, stiffness: 400 }}
                          />
                        )}
                        
                        <div className="relative z-10 flex items-center gap-3 sm:gap-4 flex-1">
                          <Icon
                            size={window.innerWidth < 640 ? 20 : 22}
                            weight={isActive ? 'bold' : 'regular'}
                            className={cn(
                              'flex-shrink-0 transition-transform duration-200',
                              !isActive && 'group-hover:scale-110'
                            )}
                          />
                          <div className="flex-1 text-left">
                            <div className="flex items-center gap-1.5 sm:gap-2">
                              <span className="font-medium text-[13px] sm:text-[15px]">{item.label}</span>
                              {item.highlight && !isActive && (
                                <Badge variant="outline" className="text-[9px] sm:text-[10px] px-1 sm:px-1.5 py-0 h-3.5 sm:h-4">
                                  NEW
                                </Badge>
                              )}
                              {showBadge && (
                                <span className={cn(
                                  'px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-mono font-semibold',
                                  isActive 
                                    ? 'bg-primary-foreground/20 text-primary-foreground'
                                    : 'bg-accent text-accent-foreground'
                                )}>
                                  {selectedItemsCount}
                                </span>
                              )}
                            </div>
                            <p className={cn(
                              'text-[10px] sm:text-xs mt-0.5',
                              isActive ? 'text-primary-foreground/80' : 'text-muted-foreground'
                            )}>
                              {item.description}
                            </p>
                          </div>
                        </div>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </nav>

            <div className="p-3 sm:p-4 border-t border-border bg-muted/30">
              <div className="text-[10px] sm:text-xs text-muted-foreground text-center space-y-0.5 sm:space-y-1">
                <p className="font-medium">Generational Economic Timeline</p>
                <p className="hidden sm:block">Build understanding through transparent data</p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
