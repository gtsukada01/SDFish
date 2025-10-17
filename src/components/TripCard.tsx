import React from 'react'
import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Calendar, Ship, MapPin, Clock, Users, Fish } from 'lucide-react'
import { CatchRecord } from '../../scripts/api/types'

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

        {/* Top Species */}
        <div className="pt-2 border-t">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium">Top Species</span>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-medium">
                {trip.top_species}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {trip.top_species_count} caught
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
