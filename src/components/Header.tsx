import React from 'react'

interface HeaderProps {
  dataSource?: 'real' | 'mock'
}

export function Header({ dataSource }: HeaderProps) {
  return (
    <header className="border-b bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-lg font-semibold hidden lg:inline">
            Southern California Offshore Analytics
          </span>
          <span className="text-lg font-semibold lg:hidden">
            SoCal Offshore Analytics
          </span>
        </div>
        {dataSource && (
          <div className={`text-xs px-2 py-1 rounded ${dataSource === 'real' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
            {dataSource === 'real' ? '🟢 Real Data' : '🟡 Mock Data'}
          </div>
        )}
      </div>
    </header>
  )
}
