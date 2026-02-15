import { useState, useEffect } from 'react'
import { Toaster } from '@/components/ui/sonner'
import { useKV } from '@github/spark/hooks'
import { AppHeader } from '@/components/AppHeader'
import { HomeView } from '@/components/HomeView'
import { ExploreView } from '@/components/ExploreView'
import { ExpandedExploreView } from '@/components/ExpandedExploreView'
import { SourceRegistryView } from '@/components/SourceRegistryView'
import { CompareView } from '@/components/CompareView'
import { SettingsView } from '@/components/SettingsView'
import { MethodologyView } from '@/components/MethodologyView'
import { AnalyticsView } from '@/components/AnalyticsView'
import { DataSourcesView } from '@/components/DataSourcesView'
import { GenerationalDashboardView } from '@/components/GenerationalDashboardView'
import { VolatilityExplorerView } from '@/components/VolatilityExplorerView'
import { LearningModuleView } from '@/components/LearningModuleView'
import { IconShowcase } from '@/components/IconShowcase'
import { LoadingShowcase } from '@/components/LoadingStates'
import { BrandShowcase } from '@/components/BrandShowcase'
import { DataQualityMonitoringView } from '@/components/DataQualityMonitoringView'
import { AutoRemediationView } from '@/components/AutoRemediationView'
import { ConnectorTestSuite } from '@/components/ConnectorTestSuite'
import type { UserWageConfig } from '@/lib/types'

function App() {
  const [activeTab, setActiveTab] = useState('home')
  
  useEffect(() => {
    const hash = window.location.hash.replace('#', '')
    if (hash === 'analytics') {
      setActiveTab('analytics')
    } else if (hash === 'sources') {
      setActiveTab('sources')
    } else if (hash === 'registry') {
      setActiveTab('registry')
    } else if (hash === 'expanded-catalog') {
      setActiveTab('expanded-catalog')
    } else if (hash === 'generations') {
      setActiveTab('generations')
    } else if (hash === 'volatility') {
      setActiveTab('volatility')
    } else if (hash === 'learn') {
      setActiveTab('learn')
    } else if (hash === 'icons') {
      setActiveTab('icons')
    } else if (hash === 'loading') {
      setActiveTab('loading')
    } else if (hash === 'brand') {
      setActiveTab('brand')
    } else if (hash === 'monitoring') {
      setActiveTab('monitoring')
    } else if (hash === 'remediation') {
      setActiveTab('remediation')
    } else if (hash === 'test-suite') {
      setActiveTab('test-suite')
    }
  }, [])
  
  const [wageConfig, setWageConfig] = useKV<UserWageConfig>('wage-config', {
    type: 'manual',
    hourlyWage: 15.00,
    region: 'US-National'
  })

  const [selectedItems, setSelectedItems] = useKV<string[]>('selected-items', [])

  const handleToggleItem = (itemId: string) => {
    setSelectedItems((current = []) => {
      if (current.includes(itemId)) {
        return current.filter(id => id !== itemId)
      }
      return [...current, itemId]
    })
  }

  const handleRemoveItem = (itemId: string) => {
    setSelectedItems((current = []) => current.filter(id => id !== itemId))
  }

  const handleCompareItems = (itemIds: string[]) => {
    setSelectedItems(itemIds)
    setActiveTab('compare')
  }

  const handleExplore = () => {
    setActiveTab('explore')
  }

  const handleUpdateWage = (config: UserWageConfig) => {
    setWageConfig(config)
  }

  return (
    <div className="min-h-screen bg-background">
      <AppHeader
        activeTab={activeTab}
        onTabChange={setActiveTab}
        selectedItemsCount={selectedItems?.length || 0}
      />

      <main className="container mx-auto px-3 py-4 sm:px-4 sm:py-6 lg:py-8">
        {activeTab === 'home' && wageConfig && (
          <HomeView 
            wageConfig={wageConfig}
            onExplore={handleExplore}
            onCompare={handleCompareItems}
          />
        )}

        {activeTab === 'explore' && selectedItems && (
          <ExploreView
            selectedItemIds={selectedItems}
            onToggleItem={handleToggleItem}
            hourlyWage={wageConfig?.hourlyWage || 15}
          />
        )}

        {activeTab === 'compare' && selectedItems && (
          <CompareView
            selectedItemIds={selectedItems}
            onRemoveItem={handleRemoveItem}
            hourlyWage={wageConfig?.hourlyWage || 15}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsView />
        )}

        {activeTab === 'generations' && (
          <GenerationalDashboardView />
        )}

        {activeTab === 'volatility' && (
          <VolatilityExplorerView />
        )}

        {activeTab === 'learn' && (
          <LearningModuleView />
        )}

        {activeTab === 'methodology' && (
          <MethodologyView />
        )}

        {activeTab === 'settings' && wageConfig && (
          <SettingsView
            wageConfig={wageConfig}
            onUpdateWage={handleUpdateWage}
          />
        )}

        {activeTab === 'sources' && (
          <DataSourcesView />
        )}

        {activeTab === 'registry' && (
          <SourceRegistryView />
        )}

        {activeTab === 'expanded-catalog' && (
          <ExpandedExploreView
            selectedItemIds={selectedItems || []}
            onToggleItem={handleToggleItem}
            onCompare={() => setActiveTab('compare')}
          />
        )}

        {activeTab === 'icons' && (
          <IconShowcase />
        )}

        {activeTab === 'loading' && (
          <LoadingShowcase />
        )}

        {activeTab === 'brand' && (
          <BrandShowcase />
        )}

        {activeTab === 'monitoring' && (
          <DataQualityMonitoringView />
        )}

        {activeTab === 'remediation' && (
          <AutoRemediationView />
        )}

        {activeTab === 'test-suite' && (
          <ConnectorTestSuite />
        )}
      </main>

      <Toaster />
    </div>
  )
}

export default App