import React from 'react'
import { ChevronDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible'
import { Button } from './ui/button'
import { SummaryMetricsResponse } from '../../scripts/api/types'

interface MetricsBreakdownProps {
  metrics: SummaryMetricsResponse
}

export function MetricsBreakdown({ metrics }: MetricsBreakdownProps) {
  const [boatOpen, setBoatOpen] = React.useState(false)

  const sortedBoats = [...metrics.per_boat].sort((a, b) => b.total_fish - a.total_fish)
  const maxFish = Math.max(...sortedBoats.map(b => b.total_fish))

  return (
    <Collapsible open={boatOpen} onOpenChange={setBoatOpen}>
      <Card>
        <CardHeader className="pb-3">
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-0 hover:bg-transparent">
              <CardTitle className="text-base">Per-Boat Breakdown</CardTitle>
              <ChevronDown
                className={`h-4 w-4 transition-transform duration-200 ${
                  boatOpen ? 'rotate-180' : ''
                }`}
              />
            </Button>
          </CollapsibleTrigger>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="space-y-3">
            {sortedBoats.map((boat) => {
              const percentage = (boat.total_fish / maxFish) * 100
              return (
                <div key={boat.boat} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{boat.boat}</span>
                    <span className="text-muted-foreground">
                      {boat.total_fish.toLocaleString()} fish · {boat.trips} trips
                    </span>
                  </div>
                  <div className="relative h-8 bg-muted rounded-md overflow-hidden">
                    <div
                      className="absolute inset-y-0 left-0 bg-primary transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                    <div className="absolute inset-0 flex items-center px-3">
                      <span className="text-xs font-medium text-primary-foreground mix-blend-difference">
                        {boat.top_species} ({boat.top_species_count.toLocaleString()})
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
