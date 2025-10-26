import React, { useState, useEffect, useRef } from 'react'
import { format } from 'date-fns'
import { Fish, Ship, Anchor, Layers, Moon, Users, Trophy, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'
import { FishingHook } from './components/icons/FishingHook'
import { CatchRecord, SummaryMetricsResponse, Filters } from '../../scripts/api/types'
import { fetchRealCatchData, fetchRealSummaryMetrics } from './lib/fetchRealData'
import { mockCatchTableResponse, mockSummaryMetricsResponse } from '../../scripts/api/mocks'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import { Sheet, SheetContent } from './components/ui/sheet'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { HeaderFilters } from './components/HeaderFilters'
import { ActiveFilters } from './components/ActiveFilters'
import { MetricsBreakdown } from './components/MetricsBreakdown'
import { MoonPhaseBreakdown } from './components/MoonPhaseBreakdown'
import { CatchTable } from './components/CatchTable'
import { normalizeSpeciesName, formatYOYChange } from './lib/utils'

type TrendMetric = ReturnType<typeof formatYOYChange>
type TrendSummary = {
  catch: TrendMetric
  trips: TrendMetric
  fleet: TrendMetric
  species: TrendMetric
  avgPerAngler: TrendMetric
}

function App() {
  const [catchData, setCatchData] = useState<CatchRecord[]>([])
  const [metrics, setMetrics] = useState<SummaryMetricsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dataSource, setDataSource] = useState<'real' | 'mock'>('mock')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('boats')
  const [isFiltersCollapsed, setIsFiltersCollapsed] = useState(false)
  const [timeframeMetrics, setTimeframeMetrics] = useState<TrendSummary | null>(null)
  const breakdownRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Default filters: YTD (Year to Date - Jan 1 to today, using local timezone, not UTC)
  const getLocalDateString = (date: Date): string => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const [filters, setFilters] = useState<Filters>({
    start_date: getLocalDateString(new Date(new Date().getFullYear(), 0, 1)), // January 1st of current year
    end_date: getLocalDateString(new Date()),
  })
  const [selectedLandings, setSelectedLandings] = useState<string[]>([])

  const summarizeRecords = (records: CatchRecord[]) => {
    const totalTrips = records.length
    const totalFish = records.reduce((sum, trip) => sum + (trip.total_fish || 0), 0)
    const uniqueBoats = new Set(records.map(trip => trip.boat)).size
    const totalAnglers = records.reduce((sum, trip) => sum + (trip.angler_count || 0), 0)
    const avgPerAngler = totalAnglers > 0 ? Math.round(totalFish / totalAnglers) : 0
    const uniqueSpeciesSet = new Set<string>()
    records.forEach(trip => {
      trip.species_breakdown?.forEach(speciesEntry => {
        const normalized = normalizeSpeciesName(speciesEntry.species)
        uniqueSpeciesSet.add(normalized)
      })
    })
    const uniqueSpecies = uniqueSpeciesSet.size

    return { totalTrips, totalFish, uniqueBoats, uniqueSpecies, avgPerAngler }
  }

  const computePreviousRange = (start: string, end: string) => {
    const startDate = new Date(start)
    const endDate = new Date(end)
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      return null
    }

    const toISO = (date: Date) => date.toISOString().split('T')[0]

    const shiftOneYear = (source: Date) => {
      const year = source.getFullYear() - 1
      const month = source.getMonth()
      const candidate = new Date(source)
      candidate.setFullYear(year)

      if (candidate.getMonth() !== month) {
        // Clamp to last day of the original month (handles leap years)
        return new Date(year, month + 1, 0)
      }

      return candidate
    }

    const prevStart = shiftOneYear(startDate)
    const prevEnd = shiftOneYear(endDate)

    if (Number.isNaN(prevStart.getTime()) || Number.isNaN(prevEnd.getTime())) {
      return null
    }

    return {
      start: toISO(prevStart),
      end: toISO(prevEnd)
    }
  }

  // Load data when filters change (no debounce - filters only change when dropdowns close)
  useEffect(() => {
    loadData()
  }, [filters, selectedLandings])

  // Scroll detection for collapsing filter section on mobile
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return

    const COLLAPSE_THRESHOLD = 50 // pixels - scroll down to collapse
    const EXPAND_THRESHOLD = 30 // pixels - must scroll back above this to expand
    let lastScrollTop = 0
    let collapsed = isFiltersCollapsed // Initialize from state to sync with manual expand/collapse
    let ticking = false

    const handleScroll = () => {
      const scrollTop = scrollContainer.scrollTop

      if (!ticking) {
        window.requestAnimationFrame(() => {
          // Scroll down past threshold = collapse
          if (scrollTop > COLLAPSE_THRESHOLD && !collapsed) {
            collapsed = true
            setIsFiltersCollapsed(true)
          }
          // Scroll up and back above expand threshold = expand
          else if (scrollTop < EXPAND_THRESHOLD && collapsed) {
            collapsed = false
            setIsFiltersCollapsed(false)
          }

          lastScrollTop = scrollTop
          ticking = false
        })
        ticking = true
      }
    }

    scrollContainer.addEventListener('scroll', handleScroll, { passive: true })
    return () => scrollContainer.removeEventListener('scroll', handleScroll)
  }, [isLoading, isFiltersCollapsed]) // Re-sync when filters are manually toggled

  const isSpeciesFiltered = !!filters.species && filters.species.length > 0

  async function loadData() {
      setIsLoading(true)
      setError(null)
      setTimeframeMetrics(null)

      // Check if real data mode is enabled (set in index.html)
      const useRealData = (window as any).USE_REAL_DATA === true

      try {
        if (useRealData) {
          // Fetch real data from Supabase
          // Convert selectedLandings array to single landing for API (use first if multiple)
          const activeLanding = selectedLandings.length > 0 ? selectedLandings[0] : undefined

          const params = {
            startDate: filters.start_date!,
            endDate: filters.end_date!,
            landing: activeLanding,
            boat: filters.boat,
            species: filters.species,
            tripDuration: filters.trip_duration || undefined,
            moonPhase: filters.moon_phase || undefined
          }

          const previousRange = computePreviousRange(params.startDate, params.endDate)
          const previousParams = previousRange
            ? {
                ...params,
                startDate: previousRange.start,
                endDate: previousRange.end
              }
            : null

          const [data, metricsData, previousData] = await Promise.all([
            fetchRealCatchData(params),
            fetchRealSummaryMetrics(params),
            previousParams ? fetchRealCatchData(previousParams) : Promise.resolve<CatchRecord[]>([])
          ])

          setCatchData(data)
          setMetrics(metricsData)
          setDataSource('real')

          const currentSummary = summarizeRecords(data)
          const previousSummary = summarizeRecords(previousData)
          setTimeframeMetrics({
            catch: formatYOYChange(currentSummary.totalFish, previousSummary.totalFish),
            trips: formatYOYChange(currentSummary.totalTrips, previousSummary.totalTrips),
            fleet: formatYOYChange(currentSummary.uniqueBoats, previousSummary.uniqueBoats),
            species: formatYOYChange(currentSummary.uniqueSpecies, previousSummary.uniqueSpecies),
            avgPerAngler: formatYOYChange(currentSummary.avgPerAngler, previousSummary.avgPerAngler)
          })
        } else {
          // Use mock data (current behavior)
          setCatchData(mockCatchTableResponse.data)
          setMetrics(mockSummaryMetricsResponse)
          setDataSource('mock')
        }
      } catch (err) {
        console.error('Data loading error:', err)
        // Fallback to mocks on error
        console.warn('⚠️  Falling back to mock data due to error')
        setCatchData(mockCatchTableResponse.data)
        setMetrics(mockSummaryMetricsResponse)
        setDataSource('mock')
        setError(err instanceof Error ? err.message : 'Failed to load real data, using mocks')
      } finally {
        setIsLoading(false)
      }
    }

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const handleLandingsChange = (landings: string[]) => {
    setSelectedLandings(landings)
  }

  const handleRemoveLanding = (landing: string) => {
    setSelectedLandings(prev => prev.filter(l => l !== landing))
  }

  const handleRemoveBoat = (boat?: string) => {
    if (!boat) {
      // Remove all boats
      setFilters(prev => ({ ...prev, boat: undefined }))
    } else {
      // Remove specific boat from array
      const boats = Array.isArray(filters.boat) ? filters.boat : filters.boat ? [filters.boat] : []
      const newBoats = boats.filter(b => b !== boat)
      setFilters(prev => ({ ...prev, boat: newBoats.length > 0 ? newBoats : undefined }))
    }
  }

  const handleRemoveSpecies = (species?: string) => {
    if (!species) {
      // Remove all species
      setFilters(prev => ({ ...prev, species: undefined }))
    } else {
      // Remove all variants of the normalized species name
      const currentSpecies = filters.species || []
      const newSpecies = currentSpecies.filter(s => normalizeSpeciesName(s) !== species)
      setFilters(prev => ({ ...prev, species: newSpecies.length > 0 ? newSpecies : undefined }))
    }
  }

  const handleRemoveMoonPhase = () => {
    setFilters(prev => ({ ...prev, moon_phase: undefined }))
  }

  const handleRemoveDateRange = () => {
    const defaultFilters: Filters = {
      start_date: getLocalDateString(new Date(new Date().getFullYear(), 0, 1)), // YTD: January 1st of current year
      end_date: getLocalDateString(new Date()),
    }
    setFilters(prev => ({ ...prev, start_date: defaultFilters.start_date, end_date: defaultFilters.end_date }))
  }

  const handleClearAllFilters = () => {
    const defaultFilters: Filters = {
      start_date: getLocalDateString(new Date(new Date().getFullYear(), 0, 1)),
      end_date: getLocalDateString(new Date()),
    }
    setFilters(defaultFilters)
    setSelectedLandings([])
  }

  const handleLogoClick = () => {
    // Reset to home: clear all filters and scroll to top
    handleClearAllFilters()
    // Scroll to top of page
    scrollContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Handle metric card clicks - switch to appropriate tab and scroll
  const handleMetricCardClick = (tab: 'boats' | 'species' | 'moon') => {
    setActiveTab(tab)
    // Wait for tab to render, then scroll smoothly
    setTimeout(() => {
      breakdownRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }, 100)
  }

  // Handle boat bar click - drilldown to specific boat
  const handleBoatBarClick = (boatName: string) => {
    console.log('[Analytics Drilldown] Boat clicked:', boatName)
    // Replace boat filter (single-select)
    setFilters(prev => ({ ...prev, boat: boatName }))

    // Scroll to table for immediate feedback
    setTimeout(() => {
      const tableElement = document.querySelector('.catch-table')
      if (tableElement) {
        tableElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }, 100)
  }

  // Handle species bar click - drilldown to specific species
  const handleSpeciesBarClick = (speciesName: string) => {
    // Normalize species name (e.g., "bluefin tuna (up to 50 pounds)" → "bluefin tuna")
    const normalized = normalizeSpeciesName(speciesName)
    console.log('[Analytics Drilldown] Species clicked:', speciesName, '→', normalized)

    // Replace species filter (single-select, wrapped in array for API compatibility)
    setFilters(prev => ({ ...prev, species: [normalized] }))

    // Scroll to table for immediate feedback
    setTimeout(() => {
      const tableElement = document.querySelector('.catch-table')
      if (tableElement) {
        tableElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }, 100)
  }

  // Handle moon phase bar click - drilldown to specific moon phase
  const handleMoonPhaseBarClick = (phaseName: string) => {
    console.log('[Analytics Drilldown] Moon phase clicked:', phaseName)
    // Replace moon phase filter (single-select)
    setFilters(prev => ({ ...prev, moon_phase: phaseName }))

    // Scroll to table for immediate feedback
    setTimeout(() => {
      const tableElement = document.querySelector('.catch-table')
      if (tableElement) {
        tableElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }, 100)
  }

  // Handle month bar click in species monthly breakdown - drilldown to specific month
  const handleMonthBarClick = (monthLabel: string) => {
    // Parse month label (e.g., "April 2025" → { year: 2025, month: 4 })
    const date = new Date(monthLabel + ' 1') // Add day for valid date parsing
    const year = date.getFullYear()
    const month = date.getMonth() + 1 // 0-indexed, so +1

    // Calculate start and end dates for the month
    const startDate = `${year}-${String(month).padStart(2, '0')}-01`
    const lastDay = new Date(year, month, 0).getDate() // Last day of month
    const endDate = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

    console.log('[Analytics Drilldown] Month clicked:', monthLabel, '→', { startDate, endDate })

    // Update date range filter to this month (keep species filter active)
    setFilters(prev => ({
      ...prev,
      start_date: startDate,
      end_date: endDate
    }))

    // Scroll to table for immediate feedback
    setTimeout(() => {
      const tableElement = document.querySelector('.catch-table')
      if (tableElement) {
        tableElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }, 100)
  }

  // Calculate conditional metrics for boat-specific view
  const isBoatFiltered = !!filters.boat || selectedLandings.length > 0

  const totalAnglers = catchData.reduce((sum, trip) =>
    sum + (trip.angler_count || 0), 0
  )
  const avgFishPerAngler = totalAnglers > 0
    ? Math.round((metrics?.fleet.total_fish || 0) / totalAnglers)
    : 0

  // Best Moon Phase - only consider phases with minimum 1 trip for statistical validity
  const MIN_TRIPS_FOR_MOON_PHASE = 1
  const filteredPhases = metrics?.moon_phase?.filter(phase => phase.trip_count >= MIN_TRIPS_FOR_MOON_PHASE) || []
  const bestMoonPhase = filteredPhases.length > 0
    ? filteredPhases.reduce((best, current) =>
        current.avg_fish_per_trip > best.avg_fish_per_trip ? current : best
      )
    : null

  // Trend Badge Component (timeframe-over-timeframe deltas)
  const TrendBadge = ({ trend }: { trend: TrendMetric }) => {
    const Icon = trend.direction === 'up' ? ArrowUpRight : trend.direction === 'down' ? ArrowDownRight : Minus
    const iconColor = trend.direction === 'up'
      ? 'text-emerald-600 dark:text-emerald-400'
      : trend.direction === 'down'
      ? 'text-red-600 dark:text-red-400'
      : 'text-muted-foreground'

    return (
      <div className="flex items-center justify-center gap-1 md:gap-1.5 text-base font-normal text-muted-foreground">
        <Icon className={`h-4 w-4 md:h-5 md:w-5 flex-shrink-0 ${iconColor}`} />
        <span className="md:hidden">{trend.displayTextCompact}</span>
        <span className="hidden md:inline">{trend.displayText}</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        onMobileMenuClick={() => setIsSidebarOpen(true)}
        onLogoClick={handleLogoClick}
      />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Sheet (both mobile and desktop) */}
        <Sheet open={isSidebarOpen} onOpenChange={setIsSidebarOpen}>
          <SheetContent side="left" className="p-0 w-[280px]">
            <Sidebar
              selectedLandings={selectedLandings}
              onLandingsChange={handleLandingsChange}
              isMobile={true}
              onClose={() => setIsSidebarOpen(false)}
            />
          </SheetContent>
        </Sheet>

        <div className="flex flex-col flex-1 overflow-hidden">
          <HeaderFilters
            filters={filters}
            onFiltersChange={setFilters}
            selectedLandings={selectedLandings}
            isCollapsed={isFiltersCollapsed}
            onToggleCollapse={() => setIsFiltersCollapsed(false)}
          />
          <ActiveFilters
            filters={filters}
            selectedLandings={selectedLandings}
            onRemoveLanding={handleRemoveLanding}
            onRemoveBoat={handleRemoveBoat}
            onRemoveSpecies={handleRemoveSpecies}
            onRemoveMoonPhase={handleRemoveMoonPhase}
            onRemoveDateRange={handleRemoveDateRange}
            onClearAll={handleClearAllFilters}
          />
          <div ref={scrollContainerRef} className="flex-1 overflow-auto">
            <div className="container mx-auto p-4 md:p-6 space-y-6">
              {/* Summary Metrics - Conditional Cards */}
              {metrics && (
                <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
                  {/* CARD 1: Catch - Always visible */}
                  <Card
                    className="relative overflow-hidden bg-gradient-to-br from-white to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                    onClick={() => handleMetricCardClick('species')}
                  >
                    <CardContent className="relative pt-6 pb-6 flex flex-col items-center justify-center min-h-[140px]">
                      <div className="absolute top-3 left-6 flex items-center gap-2">
                        <Trophy className="h-5 w-5 text-muted-foreground/60 stroke-[1.5]" />
                        <span className="text-base font-medium text-muted-foreground">Catch</span>
                      </div>
                      <div className="flex flex-col items-center justify-center gap-1 mt-6">
                        <div className="text-3xl md:text-5xl font-bold tracking-tight">
                          {metrics.fleet.total_fish.toLocaleString()}
                        </div>
                        {timeframeMetrics && <TrendBadge trend={timeframeMetrics.catch} />}
                      </div>
                    </CardContent>
                  </Card>

                  {/* CARD 2: Trips - Always visible */}
                  <Card
                    className="relative overflow-hidden bg-gradient-to-br from-white to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                    onClick={() => handleMetricCardClick('boats')}
                  >
                    <CardContent className="relative pt-6 pb-6 flex flex-col items-center justify-center min-h-[140px]">
                      <div className="absolute top-3 left-6 flex items-center gap-2">
                        <Anchor className="h-5 w-5 text-muted-foreground/60 stroke-[1.5]" />
                        <span className="text-base font-medium text-muted-foreground">Trips</span>
                      </div>
                      <div className="flex flex-col items-center justify-center gap-1 mt-6">
                        <div className="text-3xl md:text-5xl font-bold tracking-tight">
                          {metrics.fleet.total_trips.toLocaleString()}
                        </div>
                        {timeframeMetrics && <TrendBadge trend={timeframeMetrics.trips} />}
                      </div>
                    </CardContent>
                  </Card>

                  {/* CARD 3: Conditional based on boat/landing filter */}
                  {isBoatFiltered ? (
                    /* CARD 3 (Boat View): Avg Fish/Angler */
                    <Card
                      className="relative overflow-hidden bg-gradient-to-br from-white to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                      onClick={() => handleMetricCardClick('species')}
                    >
                      <CardContent className="relative pt-6 pb-6 flex flex-col items-center justify-center min-h-[140px]">
                        <div className="absolute top-3 left-6 flex items-center gap-2">
                          <Users className="h-5 w-5 text-muted-foreground/60 stroke-[1.5]" />
                          <span className="text-base font-medium text-muted-foreground">Avg / Angler</span>
                        </div>
                        <div className="flex flex-col items-center justify-center gap-1 mt-6">
                          <div className="text-3xl md:text-5xl font-bold tracking-tight">
                            {avgFishPerAngler}
                          </div>
                          {timeframeMetrics && <TrendBadge trend={timeframeMetrics.avgPerAngler} />}
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    /* CARD 3 (Default View): Fleet */
                    <Card
                      className="relative overflow-hidden bg-gradient-to-br from-white to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                      onClick={() => handleMetricCardClick('boats')}
                    >
                      <CardContent className="relative pt-6 pb-6 flex flex-col items-center justify-center min-h-[140px]">
                        <div className="absolute top-3 left-6 flex items-center gap-2">
                          <Ship className="h-5 w-5 text-muted-foreground/60 stroke-[1.5]" />
                          <span className="text-base font-medium text-muted-foreground">Fleet</span>
                        </div>
                        <div className="flex flex-col items-center justify-center gap-1 mt-6">
                          <div className="text-3xl md:text-5xl font-bold tracking-tight">
                            {metrics.fleet.unique_boats}
                          </div>
                          {timeframeMetrics && <TrendBadge trend={timeframeMetrics.fleet} />}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* CARD 4: Conditional based on boat/landing OR species filter */}
                  {isBoatFiltered || isSpeciesFiltered ? (
                    /* CARD 4 (Filtered View): Best Moon Phase */
                    <Card
                      className="relative overflow-hidden bg-gradient-to-br from-white to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                      onClick={() => handleMetricCardClick('moon')}
                    >
                      <CardContent className="relative pt-6 pb-6 flex flex-col items-center justify-center min-h-[140px]">
                        <div className="absolute top-3 left-6 flex items-center gap-2">
                          <Moon className="h-5 w-5 text-muted-foreground/60 stroke-[1.5]" />
                          <span className="text-base font-medium text-muted-foreground">Moon Phase</span>
                        </div>
                        <div className="text-center text-2xl md:text-4xl font-bold tracking-tight capitalize leading-tight px-2 mt-6">
                          {bestMoonPhase ? bestMoonPhase.phase_name.replace(/_/g, ' ') : 'N/A'}
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    /* CARD 4 (Default View): Variety */
                    <Card
                      className="relative overflow-hidden bg-gradient-to-br from-white to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                      onClick={() => handleMetricCardClick('species')}
                    >
                      <CardContent className="relative pt-6 pb-6 flex flex-col items-center justify-center min-h-[140px]">
                        <div className="absolute top-3 left-6 flex items-center gap-2">
                          <Fish className="h-5 w-5 text-muted-foreground/60 stroke-[1.5]" />
                          <span className="text-base font-medium text-muted-foreground">Species</span>
                        </div>
                        <div className="flex flex-col items-center justify-center gap-1 mt-6">
                          <div className="text-3xl md:text-5xl font-bold tracking-tight">
                            {metrics.fleet.unique_species}
                          </div>
                          {timeframeMetrics && <TrendBadge trend={timeframeMetrics.species} />}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Catch Data Table - Priority Position */}
              <CatchTable data={catchData} />

              {/* Analytics & Insights - Tabbed Section Below Table */}
              {metrics && (
                <Card ref={breakdownRef}>
                  <CardHeader>
                    <CardTitle>Analytics & Insights</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Explore detailed breakdowns and patterns in the fishing data
                    </p>
                  </CardHeader>
                  <CardContent>
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                      <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="boats">Boats</TabsTrigger>
                        <TabsTrigger value="species">{isSpeciesFiltered ? 'Monthly' : 'Species'}</TabsTrigger>
                        <TabsTrigger value="moon">Moon</TabsTrigger>
                      </TabsList>
                      <TabsContent value="boats" className="mt-6">
                        <MetricsBreakdown
                          metrics={metrics}
                          mode="boats"
                          selectedValue={filters.boat || null}
                          onBarClick={handleBoatBarClick}
                        />
                      </TabsContent>
                      <TabsContent value="species" className="mt-6">
                        <MetricsBreakdown
                          metrics={metrics}
                          mode="species"
                          selectedValue={filters.species?.[0] || null}
                          onBarClick={handleSpeciesBarClick}
                          onMonthBarClick={handleMonthBarClick}
                          catchData={catchData}
                          isSpeciesFiltered={isSpeciesFiltered}
                        />
                      </TabsContent>
                      <TabsContent value="moon" className="mt-6">
                        {metrics.moon_phase && metrics.moon_phase.length > 0 ? (
                          <MoonPhaseBreakdown
                            data={metrics.moon_phase}
                            selectedValue={filters.moon_phase || null}
                            onBarClick={handleMoonPhaseBarClick}
                          />
                        ) : (
                          <p className="text-muted-foreground text-center py-8">
                            No moon phase data available for the selected date range
                          </p>
                        )}
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
