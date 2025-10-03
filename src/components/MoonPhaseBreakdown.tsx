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

const moonIcons: Record<string, string> = {
  'new_moon': '🌑',
  'waxing_crescent': '🌒',
  'first_quarter': '🌓',
  'waxing_gibbous': '🌔',
  'full_moon': '🌕',
  'waning_gibbous': '🌖',
  'last_quarter': '🌗',
  'waning_crescent': '🌘'
}

const MOON_PHASE_ORDER = [
  'new_moon',
  'waxing_crescent',
  'first_quarter',
  'waxing_gibbous',
  'full_moon',
  'waning_gibbous',
  'last_quarter',
  'waning_crescent'
]

export function MoonPhaseBreakdown({ data }: MoonPhaseBreakdownProps) {
  const [isOpen, setIsOpen] = React.useState(false)

  if (!data || data.length === 0) {
    return null
  }

  // Sort chronologically by moon phase order
  const sortedData = [...data].sort((a, b) =>
    MOON_PHASE_ORDER.indexOf(a.phase_name) - MOON_PHASE_ORDER.indexOf(b.phase_name)
  )
  const totalFish = sortedData.reduce((sum, d) => sum + d.total_fish, 0)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CardHeader className="pb-3 pt-4">
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-0 h-auto hover:bg-transparent">
              <CardTitle className="text-base leading-none">Fish Catches by Moon Phase</CardTitle>
              <ChevronDown
                className={`h-4 w-4 transition-transform duration-200 ${
                  isOpen ? 'rotate-180' : ''
                }`}
              />
            </Button>
          </CollapsibleTrigger>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="space-y-2">
            {sortedData.map((phase) => {
              const percentage = (phase.total_fish / totalFish) * 100
              const displayName = phaseDisplayNames[phase.phase_name] || phase.phase_name
              const icon = moonIcons[phase.phase_name] || '🌑'

              return (
                <div key={phase.phase_name} className="space-y-1">
                  {/* Line 1: Icon + Progress bar + Percentage */}
                  <div className="flex items-center gap-2">
                    <span className="text-lg shrink-0 leading-none">{icon}</span>
                    <div className="relative h-7 bg-muted rounded-md overflow-hidden flex-1 flex items-center justify-end">
                      <div
                        className="absolute inset-0 left-0 bg-muted-foreground/30 transition-all duration-300"
                        style={{ width: `${percentage}%`, height: '100%' }}
                      />
                      <span className="relative text-xs font-medium text-foreground leading-none px-2">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Line 2: Phase name + metrics */}
                  <div className="text-xs text-muted-foreground">
                    {displayName}  |  {phase.total_fish.toLocaleString()} fish  |  {phase.trip_count} trips  |  {phase.avg_fish_per_trip.toFixed(1)} avg
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
