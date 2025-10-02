import React from 'react'
import { X, MapPin, Calendar, Fish, Anchor } from 'lucide-react'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Filters } from '../../scripts/api/types'
import { format } from 'date-fns'

interface ActiveFiltersProps {
  filters: Filters
  selectedLandings: string[]
  onRemoveLanding: (landing: string) => void
  onRemoveBoat: (boat?: string) => void
  onRemoveSpecies: (species?: string) => void
  onRemoveDateRange: () => void
  onClearAll: () => void
}

export function ActiveFilters({
  filters,
  selectedLandings,
  onRemoveLanding,
  onRemoveBoat,
  onRemoveSpecies,
  onRemoveDateRange,
  onClearAll
}: ActiveFiltersProps) {
  const boats = Array.isArray(filters.boat) ? filters.boat : filters.boat ? [filters.boat] : []
  const species = filters.species || []

  const hasActiveFilters =
    selectedLandings.length > 0 ||
    boats.length > 0 ||
    species.length > 0 ||
    filters.start_date ||
    filters.end_date

  if (!hasActiveFilters) {
    return null
  }

  return (
    <div className="border-b bg-background px-6 py-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Date range chip */}
          {filters.start_date && filters.end_date && (
            <Badge variant="secondary" className="gap-1.5 pr-1 h-7">
              <Calendar className="h-3 w-3" />
              <span>
                {format(new Date(filters.start_date), 'MMM d')} -{' '}
                {format(new Date(filters.end_date), 'MMM d')}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={onRemoveDateRange}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          )}

          {/* Landing chips */}
          {selectedLandings.map((landing) => (
            <Badge
              key={landing}
              variant="secondary"
              className="gap-1.5 pr-1 h-7"
            >
              <MapPin className="h-3 w-3" />
              <span className="max-w-[120px] truncate">{landing}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => onRemoveLanding(landing)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          ))}

          {/* Boat chips */}
          {boats.map((boat) => (
            <Badge key={boat} variant="secondary" className="gap-1.5 pr-1 h-7">
              <Anchor className="h-3 w-3" />
              <span className="max-w-[120px] truncate">{boat}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => onRemoveBoat(boat)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          ))}

          {/* Species chips */}
          {species.map((sp) => (
            <Badge key={sp} variant="secondary" className="gap-1.5 pr-1 h-7">
              <Fish className="h-3 w-3" />
              <span className="max-w-[120px] truncate">{sp}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => onRemoveSpecies(sp)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          ))}
        </div>

        {/* Clear All */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="h-7 text-xs"
        >
          Clear All
        </Button>
      </div>
    </div>
  )
}
