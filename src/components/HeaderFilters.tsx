import React, { useState, useEffect, useRef } from 'react'
import { format } from 'date-fns'
import { ChevronDown } from 'lucide-react'
import { Calendar } from './ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover'
import { Button } from './ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { MultiCombobox } from './ui/multi-combobox'
import { cn, normalizeSpeciesName } from '@/lib/utils'
import { Filters } from '../../scripts/api/types'
import { fetchFilterOptions } from '@/lib/fetchRealData'

type DatePreset = '7d' | '30d' | 'ytd' | '90d' | 'all' | 'custom'

function calculatePresetDates(preset: DatePreset): { start: string; end: string } {
  const today = new Date()
  const endDate = format(today, 'yyyy-MM-dd')

  switch (preset) {
    case '7d':
      return {
        start: format(new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
        end: endDate
      }
    case '30d':
      return {
        start: format(new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
        end: endDate
      }
    case 'ytd':
      return {
        start: '2025-01-01',
        end: endDate
      }
    case '90d':
      return {
        start: format(new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
        end: endDate
      }
    case 'all':
      return {
        start: '2024-01-01', // Assuming data starts from 2024
        end: endDate
      }
    default:
      return {
        start: format(new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
        end: endDate
      }
  }
}

interface HeaderFiltersProps {
  filters: Filters
  onFiltersChange: (filters: Filters) => void
  selectedLandings: string[]
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export function HeaderFilters({ filters, onFiltersChange, selectedLandings, isCollapsed = false, onToggleCollapse }: HeaderFiltersProps) {
  // Initialize selectedPreset - always start with '30d' to match App.tsx default
  const [selectedPreset, setSelectedPreset] = useState<DatePreset>('30d')
  const [showCustomCalendar, setShowCustomCalendar] = useState(false)
  const [customStartDate, setCustomStartDate] = useState<Date | undefined>(undefined)
  const [customEndDate, setCustomEndDate] = useState<Date | undefined>(undefined)
  const customButtonRef = useRef<HTMLButtonElement>(null)

  const [availableBoats, setAvailableBoats] = useState<string[]>([])
  const [availableSpecies, setAvailableSpecies] = useState<string[]>([])
  const [availableTripDurations, setAvailableTripDurations] = useState<string[]>([])
  const [speciesVariantMap, setSpeciesVariantMap] = useState<Map<string, string[]>>(new Map())
  const [loadingOptions, setLoadingOptions] = useState(true)

  // Temporary state for pending filter changes (before apply)
  const [pendingBoats, setPendingBoats] = useState<string[]>(
    Array.isArray(filters.boat) ? filters.boat : filters.boat ? [filters.boat] : []
  )
  const [pendingSpecies, setPendingSpecies] = useState<string[]>([])

  // Sync pending boat/species filters when filters prop changes from parent
  useEffect(() => {
    setPendingBoats(Array.isArray(filters.boat) ? filters.boat : filters.boat ? [filters.boat] : [])

    // Reverse map: database variants → normalized names for display
    const speciesArray = filters.species || []
    const normalizedSelected = new Set<string>()
    speciesArray.forEach(variant => {
      const normalized = normalizeSpeciesName(variant)
      normalizedSelected.add(normalized)
    })
    setPendingSpecies(Array.from(normalizedSelected))
  }, [filters.boat, filters.species])

  // Sync selectedPreset when filters change from parent (important!)
  useEffect(() => {
    if (!filters.start_date || !filters.end_date) return

    // Calculate the difference in days between start and end
    const start = new Date(filters.start_date)
    const end = new Date(filters.end_date)
    const diffDays = Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))

    // Check if it matches a preset based on day difference and end date being today-ish
    const today = new Date()
    const isRecentEndDate = Math.abs(end.getTime() - today.getTime()) < 2 * 24 * 60 * 60 * 1000 // Within 2 days

    if (isRecentEndDate) {
      if (diffDays >= 6 && diffDays <= 8) {
        setSelectedPreset('7d')
        return
      } else if (diffDays >= 28 && diffDays <= 31) {
        setSelectedPreset('30d')
        return
      } else if (diffDays >= 88 && diffDays <= 92) {
        setSelectedPreset('90d')
        return
      }
    }

    // Check YTD
    if (filters.start_date === '2025-01-01' && isRecentEndDate) {
      setSelectedPreset('ytd')
      return
    }

    // Check All Time
    if (filters.start_date === '2024-01-01' && isRecentEndDate) {
      setSelectedPreset('all')
      return
    }

    // If no preset matches, it's a custom range
    setSelectedPreset('custom')
  }, [filters.start_date, filters.end_date])


  // Load options on mount
  useEffect(() => {
    async function loadOptions() {
      try {
        const options = await fetchFilterOptions()
        setAvailableSpecies(options.species) // Normalized names for display
        setSpeciesVariantMap(options.speciesVariantMap) // Mapping for filtering
        setAvailableTripDurations(options.tripDurations)
      } catch (error) {
        console.error('Failed to load filter options:', error)
      } finally {
        setLoadingOptions(false)
      }
    }
    loadOptions()
  }, [])

  // Reload boats when landing selection changes
  useEffect(() => {
    async function loadBoats() {
      try {
        // If multiple landings selected, fetch boats for first landing (or all if none)
        const landingFilter = selectedLandings.length > 0 ? selectedLandings[0] : undefined
        const options = await fetchFilterOptions(landingFilter)
        setAvailableBoats(options.boats)
      } catch (error) {
        console.error('Failed to load boat options:', error)
      }
    }
    loadBoats()
  }, [selectedLandings])

  const handlePresetChange = (preset: string) => {
    if (preset === 'custom') {
      // Use setTimeout to ensure Select closes before opening Popover
      setTimeout(() => {
        setSelectedPreset('custom')
        setShowCustomCalendar(true)
      }, 100)
      return
    }

    const typedPreset = preset as DatePreset
    setSelectedPreset(typedPreset)
    const dates = calculatePresetDates(typedPreset)

    onFiltersChange({
      ...filters,
      start_date: dates.start,
      end_date: dates.end
    })
  }

  const handleCustomDateApply = () => {
    if (customStartDate && customEndDate) {
      setSelectedPreset('custom')
      onFiltersChange({
        ...filters,
        start_date: format(customStartDate, 'yyyy-MM-dd'),
        end_date: format(customEndDate, 'yyyy-MM-dd')
      })
      setShowCustomCalendar(false)
    }
  }

  const handleCustomCancel = () => {
    setShowCustomCalendar(false)
    // Reset to previous preset if user cancels
    if (!customStartDate || !customEndDate) {
      setSelectedPreset('30d')
    }
  }

  // Handle species filter application - expand normalized names to all variants
  const handleSpeciesApply = (selectedNormalizedNames: string[]) => {
    if (selectedNormalizedNames.length === 0) {
      onFiltersChange({ ...filters, species: undefined })
      return
    }

    // Expand normalized names to all database variants
    const allVariants: string[] = []
    selectedNormalizedNames.forEach(normalizedName => {
      const variants = speciesVariantMap.get(normalizedName) || []
      allVariants.push(...variants)
    })

    onFiltersChange({ ...filters, species: allVariants })
  }

  // Helper to format compact bar filter summary
  const getFilterSummary = () => {
    const parts: string[] = []

    // Date range
    const presetLabels: Record<DatePreset, string> = {
      '7d': 'Last 7 Days',
      '30d': 'Last 30 Days',
      'ytd': 'YTD',
      '90d': 'Last 90 Days',
      'all': 'All Time',
      'custom': 'Custom'
    }
    parts.push(presetLabels[selectedPreset])

    // Boats
    const boats = Array.isArray(filters.boat) ? filters.boat : filters.boat ? [filters.boat] : []
    parts.push(boats.length > 0 ? `${boats.length} Boat${boats.length > 1 ? 's' : ''}` : 'All Boats')

    // Species
    parts.push(pendingSpecies.length > 0 ? `${pendingSpecies.length} Species` : 'All Species')

    // Trip duration
    parts.push(filters.trip_duration || 'All Durations')

    return parts.join(' · ')
  }

  return (
    <>
      {/* Fixed-height sticky container - height never changes (prevents jitter) */}
      <div
        className="sticky top-0 z-10 border-b bg-muted/40 md:relative md:h-auto"
        style={{
          height: isCollapsed ? '48px' : '160px', // Fixed heights for each state
          overflowAnchor: 'none' // Prevent scroll anchor shifts
        }}
      >
        {/* Compact bar - only visible when collapsed */}
        <div
          className={cn(
            "absolute inset-0 md:hidden transition-opacity duration-200 ease-in-out",
            isCollapsed ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
          )}
        >
          <button
            onClick={onToggleCollapse}
            className="w-full h-full flex items-center gap-2 px-4 text-sm text-left hover:bg-muted/60 transition-colors duration-150"
          >
            <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0 transition-transform duration-200" />
            <span className="text-muted-foreground truncate">{getFilterSummary()}</span>
          </button>
        </div>

        {/* Full filters - hidden when collapsed on mobile, always visible on desktop */}
        <div
          className={cn(
            "absolute inset-0 md:relative transition-opacity duration-200 ease-in-out overflow-hidden",
            isCollapsed ? "opacity-0 pointer-events-none md:opacity-100 md:pointer-events-auto" : "opacity-100 pointer-events-auto"
          )}
        >
        <div className="container mx-auto p-4 md:px-6 py-2">
          <div className="flex items-center gap-4 flex-wrap">
        {/* Date Range Preset Selector */}
        <Select value={selectedPreset} onValueChange={handlePresetChange}>
          <SelectTrigger className="h-8 w-full md:w-[200px]">
            <span className="text-muted-foreground">
              <SelectValue placeholder="Select date range" />
            </span>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Last 7 Days</SelectItem>
            <SelectItem value="30d">Last 30 Days</SelectItem>
            <SelectItem value="ytd">YTD</SelectItem>
            <SelectItem value="90d">Last 90 Days</SelectItem>
            <SelectItem value="all">All Time</SelectItem>
            <SelectItem value="custom">Custom Range...</SelectItem>
          </SelectContent>
        </Select>

        {/* Hidden trigger button for custom date popover */}
        <Popover open={showCustomCalendar} onOpenChange={setShowCustomCalendar} modal>
          <PopoverTrigger asChild>
            <Button
              ref={customButtonRef}
              variant="ghost"
              className="sr-only"
              aria-hidden="true"
            />
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <div className="p-3 space-y-2">
              <div className="text-sm font-medium">Custom Date Range</div>
              <div className="text-xs text-muted-foreground">Start Date</div>
              <Calendar
                mode="single"
                selected={customStartDate}
                onSelect={setCustomStartDate}
              />
              <div className="text-xs text-muted-foreground mt-3">End Date</div>
              <Calendar
                mode="single"
                selected={customEndDate}
                onSelect={setCustomEndDate}
              />
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={handleCustomCancel}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleCustomDateApply}
                  disabled={!customStartDate || !customEndDate}
                >
                  Apply
                </Button>
              </div>
            </div>
          </PopoverContent>
        </Popover>

        {/* Boat Filter */}
        <MultiCombobox
          options={availableBoats}
          values={pendingBoats}
          onValuesChange={setPendingBoats}
          onApply={(values) => onFiltersChange({ ...filters, boat: values.length > 0 ? values : undefined })}
          placeholder="All Boats"
          searchPlaceholder="Search boats..."
          emptyMessage="No boats found."
          className="h-8 w-full md:w-[200px]"
          disabled={loadingOptions}
        />

        {/* Species Filter */}
        <MultiCombobox
          options={availableSpecies}
          values={pendingSpecies}
          onValuesChange={setPendingSpecies}
          onApply={handleSpeciesApply}
          placeholder="All Species"
          searchPlaceholder="Search species..."
          emptyMessage="No species found."
          className="h-8 w-full md:w-[200px]"
          disabled={loadingOptions}
        />

        {/* Trip Duration Filter */}
        <Select
          value={filters.trip_duration || 'all'}
          onValueChange={(value) => onFiltersChange({ ...filters, trip_duration: value === 'all' ? null : value })}
        >
          <SelectTrigger className="h-8 w-full md:w-[200px]">
            <span className="text-muted-foreground">
              <SelectValue placeholder="All Trip Durations" />
            </span>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Trip Durations</SelectItem>
            {availableTripDurations.map((duration) => (
              <SelectItem key={duration} value={duration}>
                {duration}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        </div>
      </div>
      </div>
      </div>

      {/* Placeholder to maintain page flow - prevents content jump on mobile */}
      <div
        className="md:hidden transition-all duration-200 ease-in-out"
        style={{
          height: isCollapsed ? '0px' : '0px' // Both 0 since sticky container handles height
        }}
      />
    </>
  )
}
