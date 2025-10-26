import React from 'react'
import { SummaryMetricsResponse, CatchRecord } from '../../scripts/api/types'
import { normalizeSpeciesName } from '@/lib/utils'

interface MetricsBreakdownProps {
  metrics: SummaryMetricsResponse
  mode?: 'boats' | 'species'
  selectedValue?: string | null  // Currently selected boat/species for visual feedback
  onBarClick?: (value: string) => void  // Callback when bar is clicked
  onMonthBarClick?: (monthLabel: string) => void  // Callback when month bar is clicked
  catchData?: CatchRecord[]  // Optional: full catch data for monthly breakdown
  isSpeciesFiltered?: boolean  // Whether a species filter is active
}

export function MetricsBreakdown({ metrics, mode = 'boats', selectedValue, onBarClick, onMonthBarClick, catchData, isSpeciesFiltered }: MetricsBreakdownProps) {
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
        .map(([key, data]) => ({
          monthKey: key,
          ...data,
          avg_per_trip: data.total_fish / data.trip_count
        }))
        .sort((a, b) => a.monthKey.localeCompare(b.monthKey))

      const maxAvg = Math.max(...monthlyData.map(m => m.avg_per_trip))
      const totalFish = monthlyData.reduce((sum, m) => sum + m.total_fish, 0)

      // Sort by performance to identify top/bottom performers
      const sortedByPerformance = [...monthlyData].sort((a, b) => b.avg_per_trip - a.avg_per_trip)

      return (
        <div className="space-y-2">
          <div className="mb-4 text-sm text-muted-foreground">
            Monthly catch breakdown for selected species · Click a month to view trips
          </div>
          {monthlyData.map((monthData) => {
            const barPercentage = (monthData.avg_per_trip / maxAvg) * 100
            const distributionPercentage = (monthData.total_fish / totalFish) * 100

            // Determine if this month is a top or bottom performer
            const performanceRank = sortedByPerformance.findIndex(m => m.monthKey === monthData.monthKey)
            const isTopPerformer = performanceRank < 2
            const isBottomPerformer = performanceRank >= sortedByPerformance.length - 2
            const barAccent = isTopPerformer
              ? 'bg-emerald-500/20'
              : isBottomPerformer
              ? 'bg-red-500/20'
              : 'bg-primary/20'

            return (
              <div
                key={monthData.monthKey}
                className={`space-y-1 rounded-md p-2 transition-colors ${
                  onMonthBarClick ? 'cursor-pointer hover:bg-accent/50' : ''
                }`}
                onClick={() => onMonthBarClick?.(monthData.month)}
                role={onMonthBarClick ? 'button' : undefined}
                tabIndex={onMonthBarClick ? 0 : undefined}
                onKeyDown={(e) => {
                  if (onMonthBarClick && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault()
                    onMonthBarClick(monthData.month)
                  }
                }}
                aria-label={`Filter by ${monthData.month}`}
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{monthData.month}</span>
                </div>
                <div className="relative h-7 bg-muted rounded-md overflow-hidden flex items-center transition-all duration-300">
                  <div
                    className={`absolute inset-0 left-0 transition-all duration-300 ${barAccent}`}
                    style={{ width: `${barPercentage}%`, height: '100%' }}
                  />
                  <span className="relative text-xs font-medium text-foreground leading-none px-3">
                    {monthData.avg_per_trip.toFixed(1)} avg/trip
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {monthData.trip_count} trips  |  {monthData.total_fish.toLocaleString()} fish  |  {distributionPercentage.toFixed(1)}%
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
      {sortedBoats.map((boat, index) => {
        const percentage = (boat.total_fish / maxFish) * 100
        const isSelected = selectedValue === boat.boat

        // Highlight best (top 2) and worst (bottom 2) performers
        const isTopPerformer = index < 2
        const isBottomPerformer = index >= sortedBoats.length - 2
        const barAccent = isTopPerformer
          ? 'bg-emerald-500/20'
          : isBottomPerformer
          ? 'bg-red-500/20'
          : 'bg-muted-foreground/30'

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
                className={`absolute inset-0 left-0 transition-all duration-300 ${barAccent}`}
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
