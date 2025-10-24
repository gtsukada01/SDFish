import React from 'react'
import { SummaryMetricsResponse, CatchRecord } from '../../scripts/api/types'
import { normalizeSpeciesName } from '@/lib/utils'

interface MetricsBreakdownProps {
  metrics: SummaryMetricsResponse
  mode?: 'boats' | 'species'
  selectedValue?: string | null  // Currently selected boat/species for visual feedback
  onBarClick?: (value: string) => void  // Callback when bar is clicked
  catchData?: CatchRecord[]  // Optional: full catch data for monthly breakdown
  isSpeciesFiltered?: boolean  // Whether a species filter is active
}

export function MetricsBreakdown({ metrics, mode = 'boats', selectedValue, onBarClick, catchData, isSpeciesFiltered }: MetricsBreakdownProps) {
  // Show species breakdown if mode is 'species'
  if (mode === 'species') {
    // When species is filtered, show monthly breakdown instead
    if (isSpeciesFiltered && catchData) {
      // Aggregate catches by month
      const monthlyMap = new Map<string, { month: string, total_fish: number, trip_count: number }>()

      catchData.forEach(trip => {
        const date = new Date(trip.trip_date)
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        const monthLabel = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })

        const current = monthlyMap.get(monthKey) || { month: monthLabel, total_fish: 0, trip_count: 0 }
        monthlyMap.set(monthKey, {
          month: monthLabel,
          total_fish: current.total_fish + trip.total_fish,
          trip_count: current.trip_count + 1
        })
      })

      // Convert to array and sort chronologically
      const monthlyData = Array.from(monthlyMap.entries())
        .map(([key, data]) => ({ monthKey: key, ...data }))
        .sort((a, b) => a.monthKey.localeCompare(b.monthKey))

      const maxFish = Math.max(...monthlyData.map(m => m.total_fish))

      return (
        <div className="space-y-2">
          <div className="mb-4 text-sm text-muted-foreground">
            Monthly catch breakdown for selected species
          </div>
          {monthlyData.map((monthData) => {
            const percentage = (monthData.total_fish / maxFish) * 100
            const avgPerTrip = (monthData.total_fish / monthData.trip_count).toFixed(1)

            return (
              <div
                key={monthData.monthKey}
                className="space-y-1 rounded-md p-2 transition-colors"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{monthData.month}</span>
                  <span className="text-muted-foreground">
                    {monthData.total_fish.toLocaleString()} fish · {monthData.trip_count} trips · {avgPerTrip} avg/trip
                  </span>
                </div>
                <div className="relative h-7 bg-muted rounded-md overflow-hidden flex items-center transition-all duration-300">
                  <div
                    className="absolute inset-0 left-0 bg-primary/20 transition-all duration-300"
                    style={{ width: `${percentage}%`, height: '100%' }}
                  />
                  <span className="relative text-xs font-medium text-foreground leading-none px-3">
                    {monthData.total_fish.toLocaleString()} caught
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )
    }

    // Default species breakdown (when no species filter active)
    // Normalize and aggregate species (group variants like "bluefin tuna (up to 50 pounds)" → "bluefin tuna")
    const speciesMap = new Map<string, number>()

    metrics.per_species.forEach(species => {
      const normalizedName = normalizeSpeciesName(species.species)
      const currentTotal = speciesMap.get(normalizedName) || 0
      speciesMap.set(normalizedName, currentTotal + species.total_fish)
    })

    // Convert map to array and sort by count descending
    const aggregatedSpecies = Array.from(speciesMap.entries())
      .map(([species, total_fish]) => ({ species, total_fish }))
      .sort((a, b) => b.total_fish - a.total_fish)

    const maxFish = Math.max(...aggregatedSpecies.map(s => s.total_fish))

    return (
      <div className="space-y-2">
        {aggregatedSpecies.map((species) => {
          const percentage = (species.total_fish / maxFish) * 100
          const isSelected = selectedValue === species.species
          return (
            <div
              key={species.species}
              className={`space-y-1 rounded-md p-2 transition-colors ${
                onBarClick ? 'cursor-pointer hover:bg-accent/50' : ''
              } ${isSelected ? 'bg-accent/30' : ''}`}
              onClick={() => onBarClick?.(species.species)}
              role={onBarClick ? 'button' : undefined}
              tabIndex={onBarClick ? 0 : undefined}
              onKeyDown={(e) => {
                if (onBarClick && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault()
                  onBarClick(species.species)
                }
              }}
              aria-label={`Filter by ${species.species}`}
            >
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{species.species}</span>
                <span className="text-muted-foreground">
                  {species.total_fish.toLocaleString()} fish
                </span>
              </div>
              <div className={`relative h-7 bg-muted rounded-md overflow-hidden flex items-center ${
                isSelected ? 'ring-2 ring-primary ring-offset-2' : ''
              } transition-all duration-300`}>
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
        const isSelected = selectedValue === boat.boat
        return (
          <div
            key={boat.boat}
            className={`space-y-1 rounded-md p-2 transition-colors ${
              onBarClick ? 'cursor-pointer hover:bg-accent/50' : ''
            } ${isSelected ? 'bg-accent/30' : ''}`}
            onClick={() => onBarClick?.(boat.boat)}
            role={onBarClick ? 'button' : undefined}
            tabIndex={onBarClick ? 0 : undefined}
            onKeyDown={(e) => {
              if (onBarClick && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault()
                onBarClick(boat.boat)
              }
            }}
            aria-label={`Filter by ${boat.boat}`}
          >
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{boat.boat}</span>
              <span className="text-muted-foreground">
                {boat.total_fish.toLocaleString()} fish · {boat.trips} trips
              </span>
            </div>
            <div className={`relative h-7 bg-muted rounded-md overflow-hidden flex items-center ${
              isSelected ? 'ring-2 ring-primary ring-offset-2' : ''
            } transition-all duration-300`}>
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
