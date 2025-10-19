import { supabase } from './supabase'
import { CatchRecord, SummaryMetricsResponse } from '../../scripts/api/types'
import { groupSpeciesByNormalizedName, normalizeSpeciesName } from './utils'

export interface FetchParams {
  startDate: string
  endDate: string
  landing?: string
  boat?: string | string[]
  species?: string[]
  tripDuration?: string
}

/**
 * Fetch real catch records from Supabase with proper schema transformation
 * Handles foreign key joins: trips → boats → landings, catches
 */
export async function fetchRealCatchData(params: FetchParams): Promise<CatchRecord[]> {
  const { startDate, endDate, landing, boat, species, tripDuration } = params

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

  // Apply trip duration filter
  if (tripDuration) {
    query = query.eq('trip_duration', tripDuration)
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
      let activeCatches = catches
      if (species && species.length > 0) {
        const matchingCatches = catches.filter((c: any) =>
          species.includes(c.species)
        )
        if (matchingCatches.length === 0) {
          return null // Will be filtered out
        }
        activeCatches = matchingCatches // Use only matching catches for calculations
      }

      // Calculate totals from ACTIVE catches (filtered or all)
      const totalFish = activeCatches.reduce((sum: number, c: any) => sum + (c.count || 0), 0)

      // Find top species from ACTIVE catches
      let topSpecies = 'N/A'
      let topSpeciesCount = 0
      if (activeCatches.length > 0) {
        const sorted = [...activeCatches].sort((a: any, b: any) =>
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
        species_breakdown: activeCatches.map((c: any) => ({
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
  speciesVariantMap: Map<string, string[]>
  tripDurations: string[]
}> {
  // Fetch all trips with boat/landing/species/duration data
  let query = supabase
    .from('trips')
    .select(`
      trip_duration,
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
    return { landings: [], boats: [], species: [], speciesVariantMap: new Map(), tripDurations: [] }
  }

  if (!data || data.length === 0) {
    return { landings: [], boats: [], species: [], speciesVariantMap: new Map(), tripDurations: [] }
  }

  // Extract unique values
  const landingSet = new Set<string>()
  const boatSet = new Set<string>()
  const speciesSet = new Set<string>()
  const tripDurationSet = new Set<string>()

  data.forEach((trip: any) => {
    const landingName = trip.boats?.landings?.name
    const boatName = trip.boats?.name

    if (landingName) landingSet.add(landingName)
    if (boatName) boatSet.add(boatName)
    if (trip.trip_duration) tripDurationSet.add(trip.trip_duration)

    if (Array.isArray(trip.catches)) {
      trip.catches.forEach((c: any) => {
        if (c.species) speciesSet.add(c.species)
      })
    }
  })

  // Group species by normalized names for cleaner display
  const allSpecies = Array.from(speciesSet)
  const { normalizedNames, variantMap } = groupSpeciesByNormalizedName(allSpecies)

  // Custom sort function for trip durations
  const sortTripDurations = (a: string, b: string): number => {
    // Define category order: Half-Day (incl. 2/4/6 Hour), 3/4 Day, Full Day, Overnight, Multi-Day, Special
    const getCategory = (duration: string): number => {
      // CRITICAL: 10 Hour = 3/4 Day, 12 Hour = Full Day
      // 2, 4, 6 Hour = Half-Day (short trips)
      if (duration === '12 Hour') return 3 // Full day
      if (duration === '10 Hour') return 2 // Three-quarter day
      if (duration.includes('Hour')) return 1 // Half-day (2, 4, 6 Hour short trips)
      if (duration.includes('1/2 Day')) return 1 // Half-day trips
      if (duration.includes('3/4 Day')) return 2 // Three-quarter day
      if (duration.includes('Full Day')) return 3 // Full day
      if (duration.includes('Overnight')) return 4 // Overnight
      if (duration.includes('Lobster')) return 6 // Special last
      return 5 // Multi-day trips (1.5, 1.75, 2, 2.5, 3, 3.5, 4, 5 Day)
    }

    const catA = getCategory(a)
    const catB = getCategory(b)

    // If different categories, sort by category
    if (catA !== catB) return catA - catB

    // Within same category, sort by numeric value or alphabetically
    if (catA === 1) {
      // Half-Day: hour-based first (2, 4, 6 Hour), then 1/2 Day (AM, PM, Twilight)
      const aIsHour = a.includes('Hour')
      const bIsHour = b.includes('Hour')

      if (aIsHour && bIsHour) {
        // Both are hour-based: sort by hour value
        const hoursA = parseInt(a.split(' ')[0])
        const hoursB = parseInt(b.split(' ')[0])
        return hoursA - hoursB
      }

      if (aIsHour && !bIsHour) return -1 // Hour trips before 1/2 Day
      if (!aIsHour && bIsHour) return 1  // 1/2 Day after Hour trips

      // Both are 1/2 Day: alphabetical (AM, PM, Twilight)
      return a.localeCompare(b)
    }

    if (catA === 2) {
      // 3/4 Day: put "3/4 Day" before "10 Hour"
      if (a.includes('3/4 Day')) return -1
      if (b.includes('3/4 Day')) return 1
      return a.localeCompare(b)
    }

    if (catA === 3) {
      // Full Day: put "Full Day" before "12 Hour"
      if (a.includes('Full Day')) return -1
      if (b.includes('Full Day')) return 1
      return a.localeCompare(b)
    }

    if (catA === 5) {
      // Multi-day: sort by day value (1.5, 1.75, 2, 2.5, 3, 3.5, 4, 5)
      const daysA = parseFloat(a.split(' ')[0])
      const daysB = parseFloat(b.split(' ')[0])
      return daysA - daysB
    }

    // For other categories (overnight, special, etc.), use alphabetical
    return a.localeCompare(b)
  }

  return {
    landings: Array.from(landingSet).sort(),
    boats: Array.from(boatSet).sort(),
    species: normalizedNames, // Return normalized names for display
    speciesVariantMap: variantMap, // Return mapping for filtering
    tripDurations: Array.from(tripDurationSet).sort(sortTripDurations)
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
    records.flatMap(r => getFilteredSpeciesBreakdown(r.species_breakdown).map(s => normalizeSpeciesName(s.species)))
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
 * Estimate the actual fishing date based on trip duration
 * Returns date when fishing likely occurred (midpoint of trip)
 *
 * @param tripDate - Return date from database (when boat came back)
 * @param tripDuration - Duration string (e.g., "1.5 Day", "1/2 Day AM")
 * @returns Estimated fishing date in YYYY-MM-DD format
 *
 * UPDATED: Now uses standardized trip durations (16 categories after normalization)
 */
function estimateFishingDate(tripDate: string, tripDuration: string): string {
  // Hours to subtract from return date to get fishing midpoint
  // Using standardized trip duration categories after normalization

  let hoursBack = 6 // Default fallback
  const duration = tripDuration || ''

  // CRITICAL: Check fractional/decimal days FIRST to avoid substring conflicts
  // (e.g., "1.5 Day" contains "5 Day", so must be checked first!)

  // Half day trips - check FIRST
  if (duration.includes('1/2 Day Twilight')) hoursBack = 3
  else if (duration.includes('1/2 Day AM')) hoursBack = 4
  else if (duration.includes('1/2 Day PM')) hoursBack = 4

  // 3/4 day trips - check BEFORE "3 Day" and "4 Day"
  else if (duration.includes('3/4 Day')) hoursBack = 6

  // Decimal day trips - check BEFORE whole number days
  // ("1.5 Day" contains "5 Day", "2.5 Day" contains "5 Day", etc.)
  else if (duration.includes('1.5 Day')) hoursBack = 24
  else if (duration.includes('1.75 Day')) hoursBack = 30
  else if (duration.includes('2.5 Day')) hoursBack = 48
  else if (duration.includes('3.5 Day')) hoursBack = 72

  // Multi-day trips - NOW safe to check whole numbers
  else if (duration.includes('5 Day')) hoursBack = 96
  else if (duration.includes('4 Day')) hoursBack = 84
  else if (duration.includes('3 Day')) hoursBack = 60
  else if (duration.includes('2 Day')) hoursBack = 36

  // Overnight trips (Reverse Overnight consolidated into Overnight)
  else if (duration.includes('Overnight')) hoursBack = 10

  // Full day trips (all geographic variants consolidated)
  else if (duration.includes('Full Day')) hoursBack = 8

  // Hour-based trips
  else if (duration.includes('12 Hour')) hoursBack = 6
  else if (duration.includes('10 Hour')) hoursBack = 5
  else if (duration.includes('6 Hour')) hoursBack = 3
  else if (duration.includes('4 Hour')) hoursBack = 2
  else if (duration.includes('2 Hour')) hoursBack = 1

  // Special cases
  else if (duration.includes('Lobster')) hoursBack = 3

  // Calculate fishing date by subtracting hours from return date
  const returnDate = new Date(tripDate + 'T12:00:00') // Assume noon return for date calculations
  const fishingDate = new Date(returnDate.getTime() - hoursBack * 60 * 60 * 1000)

  return fishingDate.toISOString().split('T')[0]
}

/**
 * Fetch moon phase data from ocean_conditions table and correlate with fishing trips
 * Uses estimated fishing date (not return date) for accurate moon phase correlation
 */
async function fetchMoonPhaseCorrelation(startDate: string, endDate: string, trips: CatchRecord[]): Promise<{
  phase_name: string
  total_fish: number
  trip_count: number
  avg_fish_per_trip: number
}[]> {
  try {
    // Expand date range to account for multi-day trips
    // Need to fetch moon data for dates earlier than startDate
    const expandedStartDate = new Date(startDate)
    expandedStartDate.setDate(expandedStartDate.getDate() - 5) // 5 days back to cover longest trips

    const { data: moonData, error } = await supabase
      .from('ocean_conditions')
      .select('date, moon_phase_name')
      .gte('date', expandedStartDate.toISOString().split('T')[0])
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

    // Aggregate trips by moon phase using ESTIMATED FISHING DATE
    const phaseMap = new Map<string, { total_fish: number; trip_count: number }>()

    trips.forEach(trip => {
      // CRITICAL: Use estimated fishing date, not return date
      // trip_duration_hours contains the string duration (e.g., "1.5 Day") despite the type annotation
      const durationString = typeof trip.trip_duration_hours === 'string'
        ? trip.trip_duration_hours
        : trip.trip_duration_hours?.toString() || ''
      const fishingDate = estimateFishingDate(trip.trip_date, durationString)
      const moonPhase = moonPhaseMap.get(fishingDate)

      if (!moonPhase) {
        return // Skip trips without moon phase data for fishing date
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
