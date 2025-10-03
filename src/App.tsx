import React, { useState, useEffect } from 'react'
import { CatchRecord, SummaryMetricsResponse, Filters } from '../scripts/api/types'
import { fetchRealCatchData, fetchRealSummaryMetrics } from './lib/fetchRealData'
import { mockCatchTableResponse, mockSummaryMetricsResponse } from '../scripts/api/mocks'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
import { Sheet, SheetContent } from './components/ui/sheet'
import { Sidebar } from './components/Sidebar'
import { Header } from './components/Header'
import { HeaderFilters } from './components/HeaderFilters'
import { ActiveFilters } from './components/ActiveFilters'
import { MetricsBreakdown } from './components/MetricsBreakdown'
import { CatchTable } from './components/CatchTable'

function App() {
  const [catchData, setCatchData] = useState<CatchRecord[]>([])
  const [metrics, setMetrics] = useState<SummaryMetricsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dataSource, setDataSource] = useState<'real' | 'mock'>('mock')
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  // Default filters: last 30 days
  const [filters, setFilters] = useState<Filters>({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
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
          console.log('Fetching real data from Supabase...')
          // Convert selectedLandings array to single landing for API (use first if multiple)
          const activeLanding = selectedLandings.length > 0 ? selectedLandings[0] : undefined

          const params = {
            startDate: filters.start_date!,
            endDate: filters.end_date!,
            landing: activeLanding,
            boat: filters.boat,
            species: filters.species
          }

          const [data, metricsData] = await Promise.all([
            fetchRealCatchData(params),
            fetchRealSummaryMetrics(params)
          ])

          setCatchData(data)
          setMetrics(metricsData)
          setDataSource('real')
          console.log(`✅ Loaded ${data.length} real trips from Supabase`)
        } else {
          // Use mock data (current behavior)
          console.log('Using mock data (set USE_REAL_DATA=true in index.html for real data)')
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
      // Remove specific species from array
      const currentSpecies = filters.species || []
      const newSpecies = currentSpecies.filter(s => s !== species)
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

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        dataSource={dataSource}
        onMobileMenuClick={() => setIsMobileSidebarOpen(true)}
      />
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop Sidebar */}
        <div className="hidden md:block">
          <Sidebar
            selectedLandings={selectedLandings}
            onLandingsChange={handleLandingsChange}
          />
        </div>

        {/* Mobile Sidebar Sheet */}
        <Sheet open={isMobileSidebarOpen} onOpenChange={setIsMobileSidebarOpen}>
          <SheetContent side="left" className="p-0 w-[280px]">
            <Sidebar
              selectedLandings={selectedLandings}
              onLandingsChange={handleLandingsChange}
              isMobile={true}
              onClose={() => setIsMobileSidebarOpen(false)}
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
            <div className="container mx-auto p-6 space-y-6">
              {/* Summary Metrics */}
      {metrics && (
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Trips
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.fleet.total_trips.toLocaleString()}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Fish
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.fleet.total_fish.toLocaleString()}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Boats
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.fleet.unique_boats}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Species
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.fleet.unique_species}</div>
            </CardContent>
          </Card>
        </div>
      )}

              {/* Metrics Breakdown */}
              {metrics && <MetricsBreakdown metrics={metrics} />}

              {/* Catch Data Table */}
              <CatchTable data={catchData} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
