import React, { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { Fish, Ship, Anchor, Layers, Moon, Users } from 'lucide-react'
import { CatchRecord, SummaryMetricsResponse, Filters } from '../scripts/api/types'
import { fetchRealCatchData, fetchRealSummaryMetrics } from './lib/fetchRealData'
import { mockCatchTableResponse, mockSummaryMetricsResponse } from '../scripts/api/mocks'
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
import { normalizeSpeciesName } from './lib/utils'

function App() {
  const [catchData, setCatchData] = useState<CatchRecord[]>([])
  const [metrics, setMetrics] = useState<SummaryMetricsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dataSource, setDataSource] = useState<'real' | 'mock'>('mock')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('boats')
  const breakdownRef = React.useRef<HTMLDivElement>(null)

  // Default filters: last 30 days (using local timezone, not UTC)
  const getLocalDateString = (date: Date): string => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const [filters, setFilters] = useState<Filters>({
    start_date: getLocalDateString(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)),
    end_date: getLocalDateString(new Date()),
  })
  const [selectedLandings, setSelectedLandings] = useState<string[]>([])

  // Load data when filters change (no debounce - filters only change when dropdowns close)
  useEffect(() => {
    loadData()
  }, [filters, selectedLandings])

  async function loadData() {
      setIsLoading(true)
      setError(null)

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
            tripDuration: filters.trip_duration || undefined
          }

          const [data, metricsData] = await Promise.all([
            fetchRealCatchData(params),
            fetchRealSummaryMetrics(params)
          ])

          setCatchData(data)
          setMetrics(metricsData)
          setDataSource('real')
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

  const handleRemoveDateRange = () => {
    const defaultFilters: Filters = {
      start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    }
    setFilters(prev => ({ ...prev, start_date: defaultFilters.start_date, end_date: defaultFilters.end_date }))
  }

  const handleClearAllFilters = () => {
    const defaultFilters: Filters = {
      start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
    }
    setFilters(defaultFilters)
    setSelectedLandings([])
  }

  // Handle metric card clicks - switch to appropriate tab and scroll
  const handleMetricCardClick = (tab: 'boats' | 'species' | 'moon') => {
    setActiveTab(tab)
    // Wait for tab to render, then scroll smoothly
    setTimeout(() => {
      breakdownRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
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

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        dataSource={dataSource}
        onMobileMenuClick={() => setIsSidebarOpen(true)}
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
          />
          <ActiveFilters
            filters={filters}
            selectedLandings={selectedLandings}
            onRemoveLanding={handleRemoveLanding}
            onRemoveBoat={handleRemoveBoat}
            onRemoveSpecies={handleRemoveSpecies}
            onRemoveDateRange={handleRemoveDateRange}
            onClearAll={handleClearAllFilters}
          />
          <div className="flex-1 overflow-auto">
            <div className="container mx-auto p-4 md:p-6 space-y-6">
              {/* Summary Metrics - Conditional Cards */}
              {metrics && (
                <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
                  {/* CARD 1: Total Fish - Always visible */}
                  <Card
                    className="relative overflow-hidden bg-gradient-to-br from-background to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                    onClick={() => handleMetricCardClick('species')}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2 mb-2">
                        <Fish className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium text-muted-foreground">Total Fish</span>
                      </div>
                      <div className="text-4xl font-bold tracking-tight mb-1">
                        {metrics.fleet.total_fish.toLocaleString()}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {isBoatFiltered ? 'Complete catch total' : 'Fleet-wide total'}
                      </p>
                    </CardContent>
                  </Card>

                  {/* CARD 2: Total Trips - Always visible */}
                  <Card
                    className="relative overflow-hidden bg-gradient-to-br from-background to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                    onClick={() => handleMetricCardClick('boats')}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2 mb-2">
                        <Anchor className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium text-muted-foreground">Total Trips</span>
                      </div>
                      <div className="text-4xl font-bold tracking-tight mb-1">
                        {metrics.fleet.total_trips.toLocaleString()}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {isBoatFiltered ? 'For selected filter' : 'Across all boats'}
                      </p>
                    </CardContent>
                  </Card>

                  {/* CARDS 3 & 4: Conditional based on filter */}
                  {isBoatFiltered ? (
                    <>
                      {/* CARD 3 (Boat View): Avg Fish/Angler */}
                      <Card className="relative overflow-hidden bg-gradient-to-br from-background to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20">
                        <CardContent className="pt-6">
                          <div className="flex items-center gap-2 mb-2">
                            <Users className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium text-muted-foreground">Avg Fish/Angler</span>
                          </div>
                          <div className="text-4xl font-bold tracking-tight mb-1">
                            {avgFishPerAngler}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Per person productivity
                          </p>
                        </CardContent>
                      </Card>

                      {/* CARD 4 (Boat View): Best Moon Phase */}
                      <Card className="relative overflow-hidden bg-gradient-to-br from-background to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20">
                        <CardContent className="pt-6">
                          <div className="flex items-center gap-2 mb-2">
                            <Moon className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium text-muted-foreground">Best Moon Phase</span>
                          </div>
                          <div className="text-4xl font-bold tracking-tight mb-1">
                            {bestMoonPhase ? bestMoonPhase.phase_name.replace(/_/g, ' ') : 'N/A'}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {bestMoonPhase
                              ? `${bestMoonPhase.avg_fish_per_trip.toFixed(1)} avg (${bestMoonPhase.trip_count} ${bestMoonPhase.trip_count === 1 ? 'trip' : 'trips'})`
                              : 'No moon phase data available'
                            }
                          </p>
                        </CardContent>
                      </Card>
                    </>
                  ) : (
                    <>
                      {/* CARD 3 (Default View): Active Boats */}
                      <Card
                        className="relative overflow-hidden bg-gradient-to-br from-background to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                        onClick={() => handleMetricCardClick('boats')}
                      >
                        <CardContent className="pt-6">
                          <div className="flex items-center gap-2 mb-2">
                            <Ship className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium text-muted-foreground">Active Boats</span>
                          </div>
                          <div className="text-4xl font-bold tracking-tight mb-1">
                            {metrics.fleet.unique_boats}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Fleet vessels
                          </p>
                        </CardContent>
                      </Card>

                      {/* CARD 4 (Default View): Species */}
                      <Card
                        className="relative overflow-hidden bg-gradient-to-br from-background to-muted/20 transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/20 cursor-pointer"
                        onClick={() => handleMetricCardClick('species')}
                      >
                        <CardContent className="pt-6">
                          <div className="flex items-center gap-2 mb-2">
                            <Layers className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium text-muted-foreground">Species</span>
                          </div>
                          <div className="text-4xl font-bold tracking-tight mb-1">
                            {metrics.fleet.unique_species}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Unique varieties
                          </p>
                        </CardContent>
                      </Card>
                    </>
                  )}
                </div>
              )}

              {/* Catch Data Table - Priority Position */}
              <CatchTable data={catchData} />

              {/* Analytics & Insights - Tabbed Section Below Table */}
              {metrics && (
                <Card ref={breakdownRef} className="border-0 shadow-none">
                  <CardHeader>
                    <CardTitle>Analytics & Insights</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Explore detailed breakdowns and patterns in the fishing data
                    </p>
                  </CardHeader>
                  <CardContent>
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                      <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="boats">Boat Breakdown</TabsTrigger>
                        <TabsTrigger value="species">Species Breakdown</TabsTrigger>
                        <TabsTrigger value="moon">Moon Phase</TabsTrigger>
                      </TabsList>
                      <TabsContent value="boats" className="mt-6">
                        <MetricsBreakdown metrics={metrics} mode="boats" />
                      </TabsContent>
                      <TabsContent value="species" className="mt-6">
                        <MetricsBreakdown metrics={metrics} mode="species" />
                      </TabsContent>
                      <TabsContent value="moon" className="mt-6">
                        {metrics.moon_phase && metrics.moon_phase.length > 0 ? (
                          <MoonPhaseBreakdown data={metrics.moon_phase} />
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
