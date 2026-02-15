import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { InlineLoader, CardLoader, DataRefreshLoader } from '@/components/LoadingStates'
import { Logo } from '@/components/Logo'

export function LoadingStateExample() {
  const [loading, setLoading] = useState(false)
  const [cardLoading, setCardLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const simulateLoad = (setter: (val: boolean) => void, duration = 2000) => {
    setter(true)
    setTimeout(() => setter(false), duration)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold font-display mb-2">Interactive Loading Examples</h2>
        <p className="text-muted-foreground">
          Click the buttons below to see loading states in action
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Inline Loading</h3>
          <div className="space-y-4">
            <Button onClick={() => simulateLoad(setLoading)}>
              Trigger Inline Loading
            </Button>
            <div className="border rounded-lg bg-muted/30 min-h-[120px]">
              {loading ? (
                <InlineLoader text="Fetching data..." />
              ) : (
                <div className="p-6 text-center text-muted-foreground">
                  Content loaded successfully
                </div>
              )}
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Card Loading</h3>
          <div className="space-y-4">
            <Button onClick={() => simulateLoad(setCardLoading)}>
              Trigger Card Loading
            </Button>
            <div className="border rounded-lg bg-muted/30 min-h-[120px]">
              {cardLoading ? (
                <div className="p-4">
                  <CardLoader text="Processing analytics..." />
                </div>
              ) : (
                <div className="p-6 text-center text-muted-foreground">
                  Card content rendered
                </div>
              )}
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Data Refresh</h3>
          <div className="space-y-4">
            <Button onClick={() => simulateLoad(setRefreshing, 1500)}>
              Refresh Data
            </Button>
            <div className="border rounded-lg bg-muted/30 p-4">
              {refreshing ? (
                <DataRefreshLoader />
              ) : (
                <div className="text-sm text-muted-foreground">
                  Data up to date
                </div>
              )}
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold font-display mb-4">Animated Logo</h3>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              The animated logo plays once on component mount
            </p>
            <div className="border rounded-lg bg-muted/30 p-8 flex justify-center">
              <Logo animated size={64} className="text-primary" />
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
