import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
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

interface DesktopNavProps {
  activeTab: string
  onTabChange: (tab: string) => void
  selectedItemsCount: number
}

const navItems = [
  { id: 'home', label: 'Home', icon: HomeIcon },
  { id: 'explore', label: 'Explore', icon: ExploreIcon },
  { id: 'expanded-catalog', label: 'Full Catalog', icon: ExploreIcon, highlight: true },
  { id: 'compare', label: 'Compare', icon: CompareIcon, badge: true },
  { id: 'analytics', label: 'Analytics', icon: AnalyticsIcon },
  { id: 'generations', label: 'Generations', icon: GenerationsIcon, highlight: true },
  { id: 'volatility', label: 'Volatility', icon: VolatilityIcon, highlight: true },
  { id: 'learn', label: 'Learn', icon: EducationIcon, highlight: true },
  { id: 'methodology', label: 'Methodology', icon: MethodologyIcon },
  { id: 'sources', label: 'Sources', icon: DataSourceIcon },
  { id: 'registry', label: 'Source Registry', icon: DataSourceIcon, highlight: true },
  { id: 'monitoring', label: 'Data Quality', icon: MonitoringIcon, highlight: true },
  { id: 'remediation', label: 'Auto-Remediation', icon: RemediationIcon, highlight: true },
  { id: 'test-suite', label: 'Test Suite', icon: TestIcon, highlight: true },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
]

export function DesktopNav({ activeTab, onTabChange, selectedItemsCount }: DesktopNavProps) {
  return (
    <nav className="flex items-center gap-1">
      {navItems.map((item) => {
        const Icon = item.icon
        const isActive = activeTab === item.id
        const showBadge = item.badge && selectedItemsCount > 0
        
        return (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={cn(
              'relative px-4 py-2 rounded-lg flex items-center gap-2 transition-all duration-200 group',
              'hover:bg-muted/60',
              isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground',
              item.highlight && !isActive && 'hover:text-accent'
            )}
          >
            {isActive && (
              <motion.div
                layoutId="desktop-active-indicator"
                className={cn(
                  "absolute inset-0 rounded-lg",
                  item.highlight 
                    ? "bg-accent/10 border-2 border-accent/30"
                    : "bg-primary/10 border-2 border-primary/20"
                )}
                initial={false}
                transition={{ type: 'spring', damping: 30, stiffness: 400 }}
              />
            )}
            
            <Icon
              size={18}
              weight={isActive ? 'bold' : 'regular'}
              className={cn(
                'relative z-10 transition-transform duration-200',
                !isActive && 'group-hover:scale-110'
              )}
            />
            <span className={cn(
              'relative z-10 font-medium text-sm whitespace-nowrap',
              isActive && 'font-semibold'
            )}>
              {item.label}
            </span>
            
            {showBadge && (
              <span className={cn(
                'relative z-10 ml-1 px-2 py-0.5 rounded-full text-xs font-mono font-semibold transition-all duration-200',
                isActive 
                  ? 'bg-primary text-primary-foreground scale-110'
                  : 'bg-accent text-accent-foreground group-hover:scale-105'
              )}>
                {selectedItemsCount}
              </span>
            )}
          </button>
        )
      })}
    </nav>
  )
}
