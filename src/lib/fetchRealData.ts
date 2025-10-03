import { supabase } from './supabase'
import { CatchRecord, SummaryMetricsResponse } from '../../scripts/api/types'

export interface FetchParams {
  startDate: string
  endDate: string
  landing?: string
  boat?: string | string[]
  species?: string[]
}

/**
 * Fetch real catch records from Supabase with proper schema transformation
 * Handles foreign key joins: trips → boats → landings, catches
 */
export async function fetchRealCatchData(params: FetchParams): Promise<CatchRecord[]> {
  const { startDate, endDate, landing, boat, species } = params

  // Build query with joins
  let query = supabase
    .from('trips')
    .select(`
      id,
      trip_date,
      trip_duration,
      anglers,
      boats!inner(id, name, landing_id, landings!inner(id, name)),
      catches!inner(species, count)
    `)
    .gte('trip_date', startDate)
    .lte('trip_date', endDate)
    .order('trip_date', { ascending: false })

  // Apply boat filter (support single or multiple boats)
  if (boat && boat !== 'all') {
    if (Array.isArray(boat)) {
      if (boat.length > 0) {
        query = query.in('boats.name', boat)
      }
    } else {
      query = query.eq('boats.name', boat)
    }
  }

  // Apply landing filter (note: landing is nested in boats.landings)
  if (landing && landing !== 'all') {
    query = query.eq('boats.landings.name', landing)
  }

  const { data, error } = await query

  if (error) {
    console.error('Supabase fetch error:', error)
    throw new Error(`Failed to fetch catch data: ${error.message}`)
  }

  if (!data || data.length === 0) {
    return []
  }

  // Transform database schema to CatchRecord format
  const records: CatchRecord[] = data
    .map((trip: any) => {
      const catches = trip.catches || []

      // Filter by species if specified
      if (species && species.length > 0) {
        const matchingCatches = catches.filter((c: any) =>
          species.includes(c.species)
        )
        if (matchingCatches.length === 0) {
          return null // Will be filtered out
        }
      }

      // Calculate totals
      const totalFish = catches.reduce((sum: number, c: any) => sum + (c.count || 0), 0)

      // Find top species
      let topSpecies = 'N/A'
      let topSpeciesCount = 0
      if (catches.length > 0) {
        const sorted = [...catches].sort((a: any, b: any) =>
          (b.count || 0) - (a.count || 0)
        )
        topSpecies = sorted[0]?.species || 'N/A'
        topSpeciesCount = sorted[0]?.count || 0
      }

      // Extract boat and landing info
      const boatData = trip.boats
      const landingData = boatData?.landings

      return {
        id: trip.id,
        trip_date: trip.trip_date,
        boat: boatData?.name || 'Unknown',
        landing: landingData?.name || 'Unknown',
        trip_duration_hours: trip.trip_duration || 0,
        angler_count: trip.anglers,
        total_fish: totalFish,
        top_species: topSpecies,
        top_species_count: topSpeciesCount,
        species_breakdown: catches.map((c: any) => ({
          species: c.species,
          count: c.count
        })),
        weather_notes: null, // Not in current schema
        created_at: new Date().toISOString()
      }
    })
    .filter((r): r is CatchRecord => r !== null)

  return records
}

/**
 * Calculate summary metrics from real catch data
 */
/**
 * Fetch unique filter options from Supabase for dropdowns
 * Returns distinct landings, boats, and species from the database
 * Optionally filters boats by landing
 */
export async function fetchFilterOptions(filterByLanding?: string): Promise<{
  landings: string[]
  boats: string[]
  species: string[]
}> {
  // Fetch all trips with boat/landing/species data
  let query = supabase
    .from('trips')
    .select(`
      boats!inner(name, landings!inner(name)),
      catches!inner(species)
    `)

  // If filtering by landing, add the constraint
  if (filterByLanding && filterByLanding !== 'all') {
    query = query.eq('boats.landings.name', filterByLanding)
  }

  const { data, error } = await query

  if (error) {
    console.error('Failed to fetch filter options:', error)
    return { landings: [], boats: [], species: [] }
  }

  if (!data || data.length === 0) {
    return { landings: [], boats: [], species: [] }
  }

  // Extract unique values
  const landingSet = new Set<string>()
  const boatSet = new Set<string>()
  const speciesSet = new Set<string>()

  data.forEach((trip: any) => {
    const landingName = trip.boats?.landings?.name
    const boatName = trip.boats?.name

    if (landingName) landingSet.add(landingName)
    if (boatName) boatSet.add(boatName)

    if (Array.isArray(trip.catches)) {
      trip.catches.forEach((c: any) => {
        if (c.species) speciesSet.add(c.species)
      })
    }
  })

  return {
    landings: Array.from(landingSet).sort(),
    boats: Array.from(boatSet).sort(),
    species: Array.from(speciesSet).sort()
  }
}

export async function fetchRealSummaryMetrics(params: FetchParams): Promise<SummaryMetricsResponse> {
  const records = await fetchRealCatchData(params)

  // Filter species breakdown if species filter is active
  const getFilteredSpeciesBreakdown = (breakdown: any[]) => {
    if (params.species && params.species.length > 0) {
      return breakdown.filter(s => params.species!.includes(s.species))
    }
    return breakdown
  }

  // Calculate fleet totals
  const totalTrips = records.length
  const totalFish = records.reduce((sum, r) => {
    const filteredBreakdown = getFilteredSpeciesBreakdown(r.species_breakdown)
    return sum + filteredBreakdown.reduce((s, sp) => s + sp.count, 0)
  }, 0)
  const uniqueBoats = new Set(records.map(r => r.boat)).size
  const allSpecies = new Set(
    records.flatMap(r => getFilteredSpeciesBreakdown(r.species_breakdown).map(s => s.species))
  )
  const uniqueSpecies = allSpecies.size

  // Fetch moon phase data and correlate with fishing trips
  const moonPhaseBreakdown = await fetchMoonPhaseCorrelation(params.startDate, params.endDate, records)

  // Calculate per-boat breakdown
  const boatMap = new Map<string, {
    trips: number
    fish: number
    topSpecies: Map<string, number>
  }>()

  records.forEach(r => {
    if (!boatMap.has(r.boat)) {
      boatMap.set(r.boat, { trips: 0, fish: 0, topSpecies: new Map() })
    }
    const boat = boatMap.get(r.boat)!
    boat.trips++

    // Only count filtered species
    const filteredBreakdown = getFilteredSpeciesBreakdown(r.species_breakdown)
    const filteredFishCount = filteredBreakdown.reduce((sum, s) => sum + s.count, 0)
    boat.fish += filteredFishCount

    filteredBreakdown.forEach(s => {
      boat.topSpecies.set(s.species, (boat.topSpecies.get(s.species) || 0) + s.count)
    })
  })

  const perBoat = Array.from(boatMap.entries())
    .map(([boat, data]) => {
      const sortedSpecies = Array.from(data.topSpecies.entries())
        .sort((a, b) => b[1] - a[1])
      return {
        boat,
        trips: data.trips,
        total_fish: data.fish,
        top_species: sortedSpecies[0]?.[0] || 'N/A',
        top_species_count: sortedSpecies[0]?.[1] || 0
      }
    })
    .sort((a, b) => b.trips - a.trips)

  // Calculate per-species breakdown (only for filtered species)
  const speciesMap = new Map<string, {
    fish: number
    boats: Set<string>
  }>()

  records.forEach(r => {
    const filteredBreakdown = getFilteredSpeciesBreakdown(r.species_breakdown)
    filteredBreakdown.forEach(s => {
      if (!speciesMap.has(s.species)) {
        speciesMap.set(s.species, { fish: 0, boats: new Set() })
      }
      const species = speciesMap.get(s.species)!
      species.fish += s.count
      species.boats.add(r.boat)
    })
  })

  const perSpecies = Array.from(speciesMap.entries())
    .map(([species, data]) => ({
      species,
      total_fish: data.fish,
      boats: data.boats.size
    }))
    .sort((a, b) => b.total_fish - a.total_fish)

  return {
    fleet: {
      total_trips: totalTrips,
      total_fish: totalFish,
      unique_boats: uniqueBoats,
      unique_species: uniqueSpecies
    },
    per_boat: perBoat,
    per_species: perSpecies,
    moon_phase: moonPhaseBreakdown,
    filters_applied: {
      start_date: params.startDate,
      end_date: params.endDate,
      species: params.species || null,
      landing: params.landing !== 'all' ? params.landing || null : null,
      boat: params.boat !== 'all' ? params.boat || null : null
    },
    last_synced_at: new Date().toISOString()
  }
}

/**
 * Fetch moon phase data from ocean_conditions table and correlate with fishing trips
 */
async function fetchMoonPhaseCorrelation(startDate: string, endDate: string, trips: CatchRecord[]): Promise<{
  phase_name: string
  total_fish: number
  trip_count: number
  avg_fish_per_trip: number
}[]> {
  try {
    // Fetch moon phase data from ocean_conditions table
    const { data: moonData, error } = await supabase
      .from('ocean_conditions')
      .select('date, moon_phase_name')
      .gte('date', startDate)
      .lte('date', endDate)

    if (error) {
      console.error('Failed to fetch moon phase data:', error)
      return []
    }

    if (!moonData || moonData.length === 0) {
      console.warn('No moon phase data available for date range')
      return []
    }

    // Create a map of date -> moon_phase_name
    const moonPhaseMap = new Map<string, string>()
    moonData.forEach((record: any) => {
      moonPhaseMap.set(record.date, record.moon_phase_name)
    })

    // Aggregate trips by moon phase
    const phaseMap = new Map<string, { total_fish: number; trip_count: number }>()

    trips.forEach(trip => {
      const moonPhase = moonPhaseMap.get(trip.trip_date)
      if (!moonPhase) {
        return // Skip trips without moon phase data
      }

      if (!phaseMap.has(moonPhase)) {
        phaseMap.set(moonPhase, { total_fish: 0, trip_count: 0 })
      }

      const phase = phaseMap.get(moonPhase)!
      phase.total_fish += trip.total_fish
      phase.trip_count += 1
    })

    // Convert to array format
    return Array.from(phaseMap.entries()).map(([phase_name, data]) => ({
      phase_name,
      total_fish: data.total_fish,
      trip_count: data.trip_count,
      avg_fish_per_trip: data.trip_count > 0 ? data.total_fish / data.trip_count : 0
    }))
  } catch (error) {
    console.error('Error fetching moon phase correlation:', error)
    return []
  }
}
