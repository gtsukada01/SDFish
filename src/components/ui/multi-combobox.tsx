import * as React from 'react'
import { Check, ChevronsUpDown, X, Ship, Fish } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from './button'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './command'
import { Popover, PopoverContent, PopoverTrigger } from './popover'
import { Badge } from './badge'

interface MultiComboboxProps {
  options: string[]
  values: string[]
  onValuesChange: (values: string[]) => void
  onApply?: (values: string[]) => void
  placeholder?: string
  emptyMessage?: string
  searchPlaceholder?: string
  className?: string
  disabled?: boolean
  icon?: React.ReactNode
}

export function MultiCombobox({
  options,
  values,
  onValuesChange,
  onApply,
  placeholder = 'Select...',
  emptyMessage = 'No results found.',
  searchPlaceholder = 'Search...',
  className,
  disabled = false,
  icon
}: MultiComboboxProps) {
  const [open, setOpen] = React.useState(false)
  const [search, setSearch] = React.useState('')
  const [pendingValues, setPendingValues] = React.useState<string[]>(values)

  // Sync pendingValues when values prop changes externally
  React.useEffect(() => {
    setPendingValues(values)
  }, [values])

  const filteredOptions = React.useMemo(() => {
    if (!search) return options
    return options.filter((option) =>
      option.toLowerCase().includes(search.toLowerCase())
    )
  }, [options, search])

  const handleSelect = (option: string) => {
    const newValues = pendingValues.includes(option)
      ? pendingValues.filter((v) => v !== option)
      : [...pendingValues, option]
    setPendingValues(newValues)
    // Don't call onValuesChange here - only update local pending state
    // Parent gets updates only when Apply is clicked
  }

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen)

    // Reset pending values to current values when opening
    if (isOpen) {
      setPendingValues(values)
      setSearch('')
    }
  }

  const handleApply = () => {
    onApply?.(pendingValues)
    setOpen(false)
  }

  const handleCancel = () => {
    setPendingValues(values) // Revert to original values
    setOpen(false)
  }

  // Check if user has made changes (enable Apply only if changed)
  const hasChanges = React.useMemo(() => {
    if (pendingValues.length !== values.length) return true
    return !pendingValues.every(v => values.includes(v))
  }, [pendingValues, values])

  const handleRemove = (option: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onValuesChange(values.filter((v) => v !== option))
  }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn('justify-start', className)}
          disabled={disabled}
        >
          {icon && <span className="mr-2 h-3.5 w-3.5 shrink-0 flex items-center">{icon}</span>}
          <span className="flex-1 text-left">
            {pendingValues.length === 0 ? (
              <span className="text-muted-foreground">{placeholder}</span>
            ) : (
              <Badge variant="secondary" className="text-xs">
                {pendingValues.length} selected
              </Badge>
            )}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder={searchPlaceholder}
            value={search}
            onValueChange={setSearch}
          />
          <CommandList className="max-h-[240px]">
            {filteredOptions.length === 0 ? (
              <CommandEmpty>{emptyMessage}</CommandEmpty>
            ) : (
              <CommandGroup>
                {filteredOptions.map((option) => (
                  <CommandItem
                    key={option}
                    value={option}
                    onSelect={(value) => {
                      handleSelect(value)
                    }}
                  >
                    <Check
                      className={cn(
                        'mr-2 h-4 w-4',
                        pendingValues.includes(option) ? 'opacity-100' : 'opacity-0'
                      )}
                    />
                    <span className="truncate">{option}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>

        {/* Footer with Apply/Cancel buttons - 2025 mobile UX best practice */}
        <div className="border-t bg-background p-2 flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="flex-1 h-11 md:h-9"
            onClick={handleCancel}
          >
            Cancel
          </Button>
          <Button
            type="button"
            size="sm"
            className="flex-1 h-11 md:h-9"
            onClick={handleApply}
            disabled={!hasChanges}
          >
            Apply {pendingValues.length > 0 && `(${pendingValues.length})`}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
