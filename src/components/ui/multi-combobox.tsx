import * as React from 'react'
import { Check, ChevronsUpDown, X } from 'lucide-react'
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
  disabled = false
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
    onValuesChange(newValues) // Update chips immediately for visual feedback
  }

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen)

    // When closing, apply the filters
    if (!isOpen && onApply) {
      onApply(pendingValues)
    }
  }

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
          className={cn('justify-between', className)}
          disabled={disabled}
        >
          <div className="flex gap-1 flex-wrap overflow-hidden">
            {pendingValues.length === 0 ? (
              <span className="text-muted-foreground">{placeholder}</span>
            ) : (
              <>
                <Badge variant="secondary" className="text-xs">
                  {pendingValues.length} selected
                </Badge>
              </>
            )}
          </div>
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
          <CommandList>
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
      </PopoverContent>
    </Popover>
  )
}
