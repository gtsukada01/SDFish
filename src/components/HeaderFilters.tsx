import React, { useState, useEffect, useRef } from 'react'
import { format } from 'date-fns'
import { Calendar } from './ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover'
import { Button } from './ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { MultiCombobox } from './ui/multi-combobox'
import { cn } from '@/lib/utils'
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
}

export function HeaderFilters({ filters, onFiltersChange, selectedLandings }: HeaderFiltersProps) {
  const [selectedPreset, setSelectedPreset] = useState<DatePreset>('30d')
  const [showCustomCalendar, setShowCustomCalendar] = useState(false)
  const [customStartDate, setCustomStartDate] = useState<Date | undefined>(undefined)
  const [customEndDate, setCustomEndDate] = useState<Date | undefined>(undefined)
  const customButtonRef = useRef<HTMLButtonElement>(null)

  const [availableBoats, setAvailableBoats] = useState<string[]>([])
  const [availableSpecies, setAvailableSpecies] = useState<string[]>([])
  const [loadingOptions, setLoadingOptions] = useState(true)

  // Temporary state for pending filter changes (before apply)
  const [pendingBoats, setPendingBoats] = useState<string[]>(
    Array.isArray(filters.boat) ? filters.boat : filters.boat ? [filters.boat] : []
  )
  const [pendingSpecies, setPendingSpecies] = useState<string[]>(filters.species || [])

  // Load options on mount
  useEffect(() => {
    async function loadOptions() {
      try {
        const options = await fetchFilterOptions()
        setAvailableSpecies(options.species)
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

    console.log('📅 Date filter changed:', {
      preset: typedPreset,
      dates,
      currentFilters: filters
    })

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

  return (
    <div className="border-b bg-muted/40 px-6 py-2">
      <div className="flex items-center gap-4 flex-wrap">
        {/* Date Range Preset Selector */}
        <Select value={selectedPreset} onValueChange={handlePresetChange}>
          <SelectTrigger className="h-8 w-full md:w-[200px]">
            <SelectValue placeholder="Select date range" />
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
          onApply={(values) => onFiltersChange({ ...filters, species: values.length > 0 ? values : undefined })}
          placeholder="All Species"
          searchPlaceholder="Search species..."
          emptyMessage="No species found."
          className="h-8 w-full md:w-[200px]"
          disabled={loadingOptions}
        />

      </div>
    </div>
  )
}
