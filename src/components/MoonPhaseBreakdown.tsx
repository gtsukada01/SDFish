import React from 'react'
import { ChevronDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible'
import { Button } from './ui/button'

interface MoonPhaseData {
  phase_name: string
  total_fish: number
  trip_count: number
  avg_fish_per_trip: number
}

interface MoonPhaseBreakdownProps {
  data: MoonPhaseData[]
}

const phaseDisplayNames: Record<string, string> = {
  'new_moon': 'New Moon',
  'waxing_crescent': 'Waxing Crescent',
  'first_quarter': 'First Quarter',
  'waxing_gibbous': 'Waxing Gibbous',
  'full_moon': 'Full Moon',
  'waning_gibbous': 'Waning Gibbous',
  'last_quarter': 'Last Quarter',
  'waning_crescent': 'Waning Crescent'
}

const chartConfig = {
  total_fish: {
    label: 'Total Fish',
    color: 'hsl(var(--chart-1))',
  },
}

export function MoonPhaseBreakdown({ data }: MoonPhaseBreakdownProps) {
  const [isOpen, setIsOpen] = React.useState(false)

  if (!data || data.length === 0) {
    return null
  }

  // Sort by total fish descending
  const sortedData = [...data].sort((a, b) => b.total_fish - a.total_fish)
  const maxFish = Math.max(...sortedData.map(d => d.total_fish))

  // Format data for chart
  const chartData = sortedData.map(item => ({
    phase: phaseDisplayNames[item.phase_name] || item.phase_name,
    total_fish: item.total_fish,
    trips: item.trip_count,
    avg: item.avg_fish_per_trip
  }))

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CardHeader className="pb-3">
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-0 hover:bg-transparent">
              <CardTitle className="text-base">Fish Catches by Moon Phase</CardTitle>
              <ChevronDown
                className={`h-4 w-4 transition-transform duration-200 ${
                  isOpen ? 'rotate-180' : ''
                }`}
              />
            </Button>
          </CollapsibleTrigger>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="space-y-3">
            {sortedData.map((phase) => {
              const percentage = (phase.total_fish / maxFish) * 100
              const displayName = phaseDisplayNames[phase.phase_name] || phase.phase_name

              return (
                <div key={phase.phase_name} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{displayName}</span>
                    <span className="text-muted-foreground">
                      {phase.total_fish.toLocaleString()} fish · {phase.trip_count} trips · {phase.avg_fish_per_trip.toFixed(1)} avg
                    </span>
                  </div>
                  <div className="relative h-8 bg-muted rounded-md overflow-hidden">
                    <div
                      className="absolute inset-y-0 left-0 bg-primary transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                    <div className="absolute inset-0 flex items-center justify-end px-3">
                      <span className="text-xs font-medium text-primary-foreground mix-blend-difference">
                        {percentage.toFixed(1)}%
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
