import { Card, CardContent, CardHeader } from './ui/card'
import { Skeleton } from './ui/skeleton'

export function DashboardSkeleton() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop Sidebar Skeleton */}
      <div className="hidden md:flex md:w-64 md:flex-col border-r bg-card">
        <div className="p-6 border-b">
          <Skeleton className="h-8 w-32" /> {/* Logo/Title */}
        </div>
        <div className="flex-1 p-4 space-y-2">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <Skeleton key={i} className="h-10 w-full" /> /* Nav items */
          ))}
        </div>
      </div>

      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Filter Bar Skeleton */}
        <div className="sticky top-0 z-10 border-b bg-muted/40">
          <div className="container mx-auto p-4 md:px-6 py-2">
            <div className="flex items-center gap-4 flex-wrap">
              <Skeleton className="h-8 w-full md:w-[200px]" /> {/* Date Range */}
              <Skeleton className="h-8 w-full md:w-[200px]" /> {/* Boats */}
              <Skeleton className="h-8 w-full md:w-[200px]" /> {/* Species */}
              <Skeleton className="h-8 w-full md:w-[200px]" /> {/* Duration */}
            </div>
          </div>
        </div>

        {/* Active Filters Skeleton */}
        <div className="border-b bg-background/50 py-2">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex items-center gap-2 flex-wrap">
              <Skeleton className="h-6 w-24" /> {/* Filter badge */}
              <Skeleton className="h-6 w-32" /> {/* Filter badge */}
              <Skeleton className="h-6 w-28" /> {/* Filter badge */}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          <div className="container mx-auto p-4 md:p-6 space-y-6">
            {/* Summary Metrics Cards Skeleton */}
            <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <Skeleton className="h-4 w-20" /> {/* Title */}
                    <Skeleton className="h-4 w-4 rounded" /> {/* Icon */}
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-8 w-24 mb-1" /> {/* Value */}
                    <Skeleton className="h-3 w-32" /> {/* Description */}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Analytics Tabs Skeleton */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-4">
                  <Skeleton className="h-6 w-32" /> {/* Tab 1 */}
                  <Skeleton className="h-6 w-32" /> {/* Tab 2 */}
                  <Skeleton className="h-6 w-32" /> {/* Tab 3 */}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Chart Skeleton */}
                <div className="space-y-2">
                  {[100, 80, 120, 60, 90, 70, 110, 85].map((height, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <Skeleton className="h-4 w-24" /> {/* Label */}
                      <Skeleton className={`h-8 flex-1 max-w-[${height}%]`} /> {/* Bar */}
                      <Skeleton className="h-4 w-12" /> {/* Value */}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Data Table Skeleton */}
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-40" /> {/* Table title */}
              </CardHeader>
              <CardContent>
                {/* Table Header */}
                <div className="border-b pb-2 mb-2">
                  <div className="grid grid-cols-4 md:grid-cols-7 gap-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full hidden md:block" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full hidden md:block" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full hidden md:block" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                </div>

                {/* Table Rows */}
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <div key={i} className="grid grid-cols-4 md:grid-cols-7 gap-2 py-3 border-b">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full hidden md:block" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full hidden md:block" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full hidden md:block" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
