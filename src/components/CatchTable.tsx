import React from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  ColumnDef,
  flexRender,
  SortingState,
} from '@tanstack/react-table'
import { ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { TripCard } from './TripCard'
import { CatchRecord } from '../../scripts/api/types'

interface CatchTableProps {
  data: CatchRecord[]
}

export function CatchTable({ data }: CatchTableProps) {
  const [sorting, setSorting] = React.useState<SortingState>([])

  const columns: ColumnDef<CatchRecord>[] = [
    {
      accessorKey: 'trip_date',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 px-2"
          >
            Date
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => {
        // Parse date as local timezone (not UTC) to prevent off-by-one day display bug
        const tripDate = row.getValue('trip_date') as string
        const [year, month, day] = tripDate.split('-').map(Number)
        const date = new Date(year, month - 1, day) // month is 0-indexed
        return <div className="font-medium text-center">{date.toLocaleDateString()}</div>
      },
    },
    {
      accessorKey: 'boat',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 px-2"
          >
            Boat
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="font-medium text-center">{row.getValue('boat')}</div>,
    },
    {
      accessorKey: 'landing',
      header: 'Landing',
      cell: ({ row }) => <div className="text-sm text-center">{row.getValue('landing')}</div>,
    },
    {
      accessorKey: 'trip_duration_hours',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 px-2"
          >
            Duration
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => <div className="text-sm text-center">{row.getValue('trip_duration_hours')}</div>,
    },
    {
      accessorKey: 'angler_count',
      header: 'Anglers',
      cell: ({ row }) => {
        const count = row.getValue('angler_count') as number | null
        return <div className="text-sm text-center">{count ?? 'N/A'}</div>
      },
    },
    {
      accessorKey: 'total_fish',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="h-8 px-2"
          >
            Total Fish
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => (
        <div className="text-sm font-semibold text-center">{row.getValue('total_fish')}</div>
      ),
    },
    {
      accessorKey: 'top_species',
      header: 'Top Species',
      cell: ({ row }) => {
        const species = row.getValue('top_species') as string
        const count = row.original.top_species_count
        return (
          <div className="space-y-1 text-center">
            <Badge variant="secondary" className="font-medium">
              {species}
            </Badge>
            <div className="text-xs text-muted-foreground">{count} caught</div>
          </div>
        )
      },
    },
    {
      accessorKey: 'weather_notes',
      header: 'Weather',
      cell: ({ row }) => {
        const notes = row.getValue('weather_notes') as string | null
        return (
          <div className="text-sm text-muted-foreground max-w-[200px] truncate text-center">
            {notes ?? 'N/A'}
          </div>
        )
      },
    },
  ]

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
    initialState: {
      pagination: {
        pageSize: 25,
      },
    },
  })

  const currentRows = table.getRowModel().rows

  return (
    <>
      {/* Desktop Table View */}
      <Card className="hidden md:block border-transparent shadow-none">
        <CardHeader>
          <CardTitle>Catch Records</CardTitle>
          <p className="text-sm text-muted-foreground">
            {data.length} total records · Page {table.getState().pagination.pageIndex + 1} of{' '}
            {table.getPageCount()}
          </p>
        </CardHeader>
        <CardContent>
          <div className="rounded-md">
            <Table className="catch-table">
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id} className="text-center">
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {currentRows?.length ? (
                  currentRows.map((row) => (
                    <TableRow key={row.id} data-state={row.getIsSelected() && 'selected'}>
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                      No results.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* Desktop Pagination */}
          <div className="flex items-center justify-between space-x-2 py-4">
            <div className="text-sm text-muted-foreground">
              Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
              {Math.min(
                (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                data.length
              )}{' '}
              of {data.length} records
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Mobile Card List View */}
      <div className="md:hidden space-y-4">
        {/* Mobile Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Catch Records</h2>
            <p className="text-sm text-muted-foreground">
              {data.length} total records
            </p>
          </div>
        </div>

        {/* Mobile Trip Cards */}
        <div className="space-y-3">
          {currentRows?.length ? (
            currentRows.map((row) => (
              <TripCard key={row.id} trip={row.original} />
            ))
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                No results.
              </CardContent>
            </Card>
          )}
        </div>

        {/* Mobile Pagination */}
        <div className="flex flex-col gap-3">
          <div className="text-sm text-muted-foreground text-center">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()} ·
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}-
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              data.length
            )} of {data.length}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
