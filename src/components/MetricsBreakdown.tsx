import React from 'react'
import { SummaryMetricsResponse } from '../../scripts/api/types'

interface MetricsBreakdownProps {
  metrics: SummaryMetricsResponse
  mode?: 'boats' | 'species'
}

export function MetricsBreakdown({ metrics, mode = 'boats' }: MetricsBreakdownProps) {
  // Show species breakdown if mode is 'species'
  if (mode === 'species') {
    // Show all species caught
    const sortedSpecies = [...metrics.per_species].sort((a, b) => b.total_fish - a.total_fish)
    const maxFish = Math.max(...sortedSpecies.map(s => s.total_fish))

    return (
      <div className="space-y-2">
        {sortedSpecies.map((species) => {
          const percentage = (species.total_fish / maxFish) * 100
          return (
            <div key={species.species} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{species.species}</span>
                <span className="text-muted-foreground">
                  {species.total_fish.toLocaleString()} fish
                </span>
              </div>
              <div className="relative h-7 bg-muted rounded-md overflow-hidden flex items-center">
                <div
                  className="absolute inset-0 left-0 bg-primary/20 transition-all duration-300"
                  style={{ width: `${percentage}%`, height: '100%' }}
                />
                <span className="relative text-xs font-medium text-foreground leading-none px-3">
                  {species.total_fish.toLocaleString()} caught
                </span>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  // Default: Show boat breakdown
  const sortedBoats = [...metrics.per_boat].sort((a, b) => b.total_fish - a.total_fish)
  const maxFish = Math.max(...sortedBoats.map(b => b.total_fish))

  return (
    <div className="space-y-2">
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
    </div>
  )
}
