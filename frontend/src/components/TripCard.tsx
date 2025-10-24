import React from 'react'
import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet'
import { Calendar, Ship, MapPin, Clock, Users, Fish } from 'lucide-react'
import { CatchRecord } from '../../scripts/api/types'
import { normalizeSpeciesName } from '@/lib/utils'
import { SpeciesList } from './SpeciesBreakdown'

interface TripCardProps {
  trip: CatchRecord
}

export function TripCard({ trip }: TripCardProps) {
  // Parse date as local timezone (not UTC) to prevent off-by-one day display bug
  // trip.trip_date is 'YYYY-MM-DD' format representing the departure date
  const [year, month, day] = trip.trip_date.split('-').map(Number)
  const date = new Date(year, month - 1, day) // month is 0-indexed
  const formattedDate = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4 space-y-3">
        {/* Header: Date and Boat */}
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1 flex-1 min-w-0">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4 shrink-0" />
              <span className="font-medium">{formattedDate}</span>
            </div>
            <div className="flex items-center gap-2">
              <Ship className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="font-semibold text-base truncate">{trip.boat}</span>
            </div>
          </div>
          <Badge variant="secondary" className="shrink-0">
            <Fish className="h-3 w-3 mr-1" />
            {trip.total_fish}
          </Badge>
        </div>

        {/* Landing */}
        <div className="flex items-center gap-2 text-sm">
          <MapPin className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="text-muted-foreground">{trip.landing}</span>
        </div>

        {/* Trip Details */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <Clock className="h-4 w-4" />
            <span>{trip.trip_duration_hours}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="h-4 w-4" />
            <span>{trip.angler_count ?? 'N/A'} anglers</span>
          </div>
        </div>

        {/* Species - Clean inline with Dialog */}
        <div className="pt-2 border-t">
          <div className="text-xs text-muted-foreground font-medium mb-1.5">Species</div>
          <SpeciesInlineMobile speciesBreakdown={trip.species_breakdown || []} />
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * SpeciesInlineMobile - Compact inline species display for mobile cards
 * Shows top 2-3 species, tap for Sheet (bottom drawer) with full breakdown
 */
function SpeciesInlineMobile({ speciesBreakdown }: { speciesBreakdown: { species: string; count: number }[] }) {
  if (!speciesBreakdown || speciesBreakdown.length === 0) {
    return <div className="text-sm text-muted-foreground">No species data</div>
  }

  const sortedSpecies = [...speciesBreakdown].sort((a, b) => b.count - a.count)
  const displayLimit = 3 // Show top 3 species on mobile
  const topSpecies = sortedSpecies.slice(0, displayLimit)
  const remainingSpecies = sortedSpecies.slice(displayLimit)
  const hasMore = remainingSpecies.length > 0

  const summaryText = topSpecies
    .map(s => `${normalizeSpeciesName(s.species)} (${s.count})`)
    .join(', ')

  return (
    <div className="text-sm">
      <span className="text-foreground">{summaryText}</span>
      {hasMore && (
        <>
          <span className="text-foreground">, </span>
          <Sheet>
            <SheetTrigger asChild>
              <button className="text-foreground underline decoration-dotted cursor-pointer transition-colors hover:opacity-80">
                +{remainingSpecies.length}
              </button>
            </SheetTrigger>
            <SheetContent side="bottom" className="max-h-[80vh]">
              <SheetHeader>
                <SheetTitle>Full Species Breakdown</SheetTitle>
              </SheetHeader>
              <div className="mt-4">
                <SpeciesList speciesBreakdown={speciesBreakdown} />
              </div>
            </SheetContent>
          </Sheet>
        </>
      )}
    </div>
  )
}
