import React from 'react'

interface MoonPhaseData {
  phase_name: string
  total_fish: number
  trip_count: number
  avg_fish_per_trip: number
}

interface MoonPhaseBreakdownProps {
  data: MoonPhaseData[]
  selectedValue?: string | null  // Currently selected moon phase for visual feedback
  onBarClick?: (phaseName: string) => void  // Callback when bar is clicked
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

export function MoonPhaseBreakdown({ data, selectedValue, onBarClick }: MoonPhaseBreakdownProps) {
  if (!data || data.length === 0) {
    return null
  }

  // Sort by performance (avg_fish_per_trip) descending - best performers first
  const sortedData = [...data].sort((a, b) => b.avg_fish_per_trip - a.avg_fish_per_trip)
  const totalFish = sortedData.reduce((sum, d) => sum + d.total_fish, 0)
  const maxAvg = Math.max(...sortedData.map(d => d.avg_fish_per_trip))

  return (
    <div className="space-y-2">
      {sortedData.map((phase, index) => {
        const barPercentage = (phase.avg_fish_per_trip / maxAvg) * 100
        const distributionPercentage = (phase.total_fish / totalFish) * 100
        const displayName = phaseDisplayNames[phase.phase_name] || phase.phase_name
        const icon = moonIcons[phase.phase_name] || '🌑'
        const isSelected = selectedValue === phase.phase_name

        // Highlight best (top 2) and worst (bottom 2) performers
        const isTopPerformer = index < 2
        const isBottomPerformer = index >= sortedData.length - 2
        const barAccent = isTopPerformer
          ? 'bg-emerald-500/20'
          : isBottomPerformer
          ? 'bg-red-500/20'
          : 'bg-muted-foreground/30'

        return (
          <div
            key={phase.phase_name}
            className={`space-y-1 rounded-md p-2 transition-colors ${
              onBarClick ? 'cursor-pointer hover:bg-accent/50' : ''
            } ${isSelected ? 'bg-accent/30' : ''}`}
            onClick={() => onBarClick?.(phase.phase_name)}
            role={onBarClick ? 'button' : undefined}
            tabIndex={onBarClick ? 0 : undefined}
            onKeyDown={(e) => {
              if (onBarClick && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault()
                onBarClick(phase.phase_name)
              }
            }}
            aria-label={`Filter by ${displayName}`}
          >
            {/* Line 1: Icon + Performance bar + Avg metric */}
            <div className="flex items-center gap-2">
              <span className="text-lg shrink-0 leading-none">{icon}</span>
              <div className={`relative h-7 bg-muted rounded-md overflow-hidden flex-1 flex items-center ${
                isSelected ? 'ring-2 ring-primary ring-offset-2' : ''
              } transition-all duration-300`}>
                <div
                  className={`absolute inset-0 left-0 transition-all duration-300 ${barAccent}`}
                  style={{ width: `${barPercentage}%`, height: '100%' }}
                />
                <span className="relative text-xs font-medium text-foreground leading-none px-3">
                  {phase.avg_fish_per_trip.toFixed(1)} avg
                </span>
              </div>
            </div>

            {/* Line 2: Phase name + metrics */}
            <div className="text-xs text-muted-foreground">
              {displayName}  |  {phase.trip_count} trips  |  {phase.total_fish.toLocaleString()} fish  |  {distributionPercentage.toFixed(1)}%
            </div>
          </div>
        )
      })}
    </div>
  )
}
