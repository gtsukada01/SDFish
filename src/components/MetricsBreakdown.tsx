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
        <CardHeader className="pb-3 pt-4">
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-0 h-auto hover:bg-transparent">
              <CardTitle className="text-base leading-none">Per-Boat Breakdown</CardTitle>
              <ChevronDown
                className={`h-4 w-4 transition-transform duration-200 ${
                  boatOpen ? 'rotate-180' : ''
                }`}
              />
            </Button>
          </CollapsibleTrigger>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="space-y-2">
            {sortedBoats.map((boat) => {
              const percentage = (boat.total_fish / maxFish) * 100
              return (
                <div key={boat.boat} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{boat.boat}</span>
                    <span className="text-muted-foreground">
                      {boat.total_fish.toLocaleString()} fish · {boat.trips} trips
                    </span>
                  </div>
                  <div className="relative h-7 bg-muted rounded-md overflow-hidden flex items-center">
                    <div
                      className="absolute inset-0 left-0 bg-muted-foreground/30 transition-all duration-300"
                      style={{ width: `${percentage}%`, height: '100%' }}
                    />
                    <span className="relative text-xs font-medium text-foreground leading-none px-3">
                      {boat.top_species} ({boat.top_species_count.toLocaleString()})
                    </span>
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
