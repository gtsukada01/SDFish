import { supabase } from './supabase'
import { CatchRecord, SummaryMetricsResponse } from '../../scripts/api/types'

export interface FetchCatchDataParams {
  startDate: string
  endDate: string
  landing?: string
  boat?: string
  species?: string[]
}

/**
 * Fetch catch records from Supabase trips table
 */
export async function fetchCatchData(params: FetchCatchDataParams): Promise<CatchRecord[]> {
  const { startDate, endDate, landing, boat, species } = params

  let query = supabase
    .from('trips')
    .select(`
      id,
      trip_date,
      trip_duration,
      anglers,
      catches,
      weather_notes,
      created_at,
      boats!inner(name, landing)
    `)
    .gte('trip_date', startDate)
    .lte('trip_date', endDate)
    .order('trip_date', { ascending: false })

  if (landing && landing !== 'all') {
    query = query.eq('boats.landing', landing)
  }

  if (boat && boat !== 'all') {
    query = query.eq('boats.name', boat)
  }

  const { data, error } = await query

  if (error) {
    console.error('Supabase fetch error:', error)
    throw new Error(`Failed to fetch catch data: ${error.message}`)
  }

  if (!data) {
    return []
  }

  // Transform Supabase data to CatchRecord format
  const records: CatchRecord[] = data.map((trip: any) => {
    const catches = trip.catches || []
    const totalFish = catches.reduce((sum: number, c: any) => sum + (c.count || 0), 0)

    // Find top species
    let topSpecies = 'N/A'
    let topSpeciesCount = 0
    if (catches.length > 0) {
      const sorted = [...catches].sort((a, b) => (b.count || 0) - (a.count || 0))
      topSpecies = sorted[0].species || 'N/A'
      topSpeciesCount = sorted[0].count || 0
    }

    // Filter by species if specified
    if (species && species.length > 0) {
      const hasSpecies = catches.some((c: any) => species.includes(c.species))
      if (!hasSpecies) {
        return null // Will be filtered out
      }
    }

    return {
      id: trip.id,
      trip_date: trip.trip_date,
      boat: trip.boats?.name || 'Unknown',
      landing: trip.boats?.landing || 'Unknown',
      trip_duration_hours: trip.trip_duration || 0,
      angler_count: trip.anglers,
      total_fish: totalFish,
      top_species: topSpecies,
      top_species_count: topSpeciesCount,
      species_breakdown: catches.map((c: any) => ({
        species: c.species,
        count: c.count
      })),
      weather_notes: trip.weather_notes,
      created_at: trip.created_at
    }
  }).filter((r): r is CatchRecord => r !== null)

  return records
}

/**
 * Fetch summary metrics from catch data
 */
export async function fetchSummaryMetrics(params: FetchCatchDataParams): Promise<SummaryMetricsResponse> {
  const records = await fetchCatchData(params)

  // Calculate fleet totals
  const totalTrips = records.length
  const totalFish = records.reduce((sum, r) => sum + r.total_fish, 0)
  const uniqueBoats = new Set(records.map(r => r.boat)).size
  const allSpecies = new Set(
    records.flatMap(r => r.species_breakdown.map(s => s.species))
  )
  const uniqueSpecies = allSpecies.size

  // Calculate per-boat breakdown
  const boatMap = new Map<string, { trips: number; fish: number; topSpecies: Map<string, number> }>()
  records.forEach(r => {
    if (!boatMap.has(r.boat)) {
      boatMap.set(r.boat, { trips: 0, fish: 0, topSpecies: new Map() })
    }
    const boat = boatMap.get(r.boat)!
    boat.trips++
    boat.fish += r.total_fish
    r.species_breakdown.forEach(s => {
      boat.topSpecies.set(s.species, (boat.topSpecies.get(s.species) || 0) + s.count)
    })
  })

  const perBoat = Array.from(boatMap.entries()).map(([boat, data]) => {
    const sortedSpecies = Array.from(data.topSpecies.entries()).sort((a, b) => b[1] - a[1])
    return {
      boat,
      trips: data.trips,
      total_fish: data.fish,
      top_species: sortedSpecies[0]?.[0] || 'N/A',
      top_species_count: sortedSpecies[0]?.[1] || 0
    }
  }).sort((a, b) => b.trips - a.trips)

  // Calculate per-species breakdown
  const speciesMap = new Map<string, { fish: number; boats: Set<string> }>()
  records.forEach(r => {
    r.species_breakdown.forEach(s => {
      if (!speciesMap.has(s.species)) {
        speciesMap.set(s.species, { fish: 0, boats: new Set() })
      }
      const species = speciesMap.get(s.species)!
      species.fish += s.count
      species.boats.add(r.boat)
    })
  })

  const perSpecies = Array.from(speciesMap.entries()).map(([species, data]) => ({
    species,
    total_fish: data.fish,
    boats: data.boats.size
  })).sort((a, b) => b.total_fish - a.total_fish)

  return {
    fleet: {
      total_trips: totalTrips,
      total_fish: totalFish,
      unique_boats: uniqueBoats,
      unique_species: uniqueSpecies
    },
    per_boat: perBoat,
    per_species: perSpecies,
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
