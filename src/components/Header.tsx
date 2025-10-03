import React from 'react'
import { Menu } from 'lucide-react'
import { Button } from './ui/button'

interface HeaderProps {
  dataSource?: 'real' | 'mock'
  onMobileMenuClick?: () => void
}

export function Header({ dataSource, onMobileMenuClick }: HeaderProps) {
  return (
    <header className="border-b bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden h-8 w-8"
            onClick={onMobileMenuClick}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div>
            <span className="text-lg font-semibold hidden lg:inline">
              Southern California Offshore Analytics
            </span>
            <span className="text-lg font-semibold lg:hidden">
              SoCal Offshore Analytics
            </span>
          </div>
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
