import React from 'react'
import { Badge } from './ui/badge'
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover'
import { normalizeSpeciesName } from '@/lib/utils'

interface SpeciesBreakdownProps {
  speciesBreakdown: {
    species: string
    count: number
  }[]
  variant?: 'table' | 'card'
}

/**
 * SpeciesBreakdown - Clean inline text summary following 2025 UX best practices
 *
 * Default: Compact inline text (top 2-3 species)
 * Detail: Click "+N" to open contextual Popover (desktop) - anchored to cell
 *
 * No badge clutter, no vertical stacking - just clean, scannable text
 */
export function SpeciesBreakdown({ speciesBreakdown, variant = 'table' }: SpeciesBreakdownProps) {
  if (!speciesBreakdown || speciesBreakdown.length === 0) {
    return <div className="text-sm text-muted-foreground">No species data</div>
  }

  // Sort by count descending
  const sortedSpecies = [...speciesBreakdown].sort((a, b) => b.count - a.count)
  const speciesCount = sortedSpecies.length

  // Show top 3 species inline, rest in Popover
  const displayLimit = 3
  const topSpecies = sortedSpecies.slice(0, displayLimit)
  const remainingSpecies = sortedSpecies.slice(displayLimit)
  const hasMore = remainingSpecies.length > 0

  // Build inline summary text
  const summaryText = topSpecies
    .map(s => `${normalizeSpeciesName(s.species)} (${s.count})`)
    .join(', ')

  return (
    <div className="text-sm">
      <span className="text-foreground">{summaryText}</span>
      {hasMore && (
        <>
          <span className="text-foreground">, </span>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-muted-foreground hover:text-foreground underline decoration-dotted cursor-pointer transition-colors">
                +{remainingSpecies.length}
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="start" side="right">
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm font-semibold border-b pb-2">
                  <span>Species</span>
                  <span>Count</span>
                </div>
                <div className="space-y-1.5 max-h-80 overflow-y-auto">
                  {sortedSpecies.map((species, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-muted/50 transition-colors text-sm"
                    >
                      <span className="font-medium">
                        {normalizeSpeciesName(species.species)}
                      </span>
                      <Badge variant="secondary" className="text-xs">{species.count}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </>
      )}
    </div>
  )
}

/**
 * SpeciesList - Simple list view for mobile cards (expandable section)
 */
export function SpeciesList({
  speciesBreakdown
}: {
  speciesBreakdown: { species: string; count: number }[]
}) {
  const sortedSpecies = [...speciesBreakdown].sort((a, b) => b.count - a.count)

  return (
    <div className="space-y-3 pt-2">
      <div className="flex items-center justify-between text-xs text-muted-foreground pb-2 border-b">
        <span>Species</span>
        <span>Count</span>
      </div>
      <div className="space-y-1.5">
        {sortedSpecies.map((species, index) => (
          <div
            key={index}
            className="flex items-center justify-between text-sm py-1.5 px-2 rounded hover:bg-muted/30"
          >
            <span className="font-medium">
              {normalizeSpeciesName(species.species)}
            </span>
            <span className="text-muted-foreground">{species.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
