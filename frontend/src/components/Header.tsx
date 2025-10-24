import React from 'react'
import { Menu } from 'lucide-react'
import { Button } from './ui/button'

interface HeaderProps {
  onMobileMenuClick?: () => void
  onLogoClick?: () => void
}

export function Header({ onMobileMenuClick, onLogoClick }: HeaderProps) {
  return (
    <header className="border-b bg-background px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onMobileMenuClick}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div
            onClick={onLogoClick}
            className="cursor-pointer transition-colors hover:text-primary"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (onLogoClick && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault()
                onLogoClick()
              }
            }}
            aria-label="Reset to home"
          >
            <span className="text-lg font-semibold hidden lg:inline">
              Southern California Offshore Analytics
            </span>
            <span className="text-lg font-semibold lg:hidden">
              SoCal Offshore Analytics
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
