import React, { useState, useEffect } from 'react'
import { ChevronRight, MapPin, Pin, PanelLeftClose, PanelLeft } from 'lucide-react'
import { Button } from './ui/button'
import { Separator } from './ui/separator'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible'
import { fetchFilterOptions } from '@/lib/fetchRealData'

interface SidebarProps {
  selectedLandings: string[]
  onLandingsChange: (landings: string[]) => void
  isMobile?: boolean
  onClose?: () => void
}

export function Sidebar({ selectedLandings, onLandingsChange, isMobile = false, onClose }: SidebarProps) {
  const [landings, setLandings] = useState<string[]>([])
  const [pinnedLandings, setPinnedLandings] = useState<Set<string>>(new Set())
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [openSections, setOpenSections] = useState({
    sanDiego: true,
    orangeCounty: false,
    losAngeles: false,
    channelIslands: false
  })

  useEffect(() => {
    async function loadLandings() {
      const options = await fetchFilterOptions()
      setLandings(options.landings)
    }
    loadLandings()
  }, [])

  const toggleSection = (section: keyof typeof openSections) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const togglePin = (landing: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setPinnedLandings(prev => {
      const next = new Set(prev)
      if (next.has(landing)) {
        next.delete(landing)
      } else {
        next.add(landing)
      }
      return next
    })
  }

  const toggleLanding = (landing: string) => {
    const isSelected = selectedLandings.includes(landing)
    if (isSelected) {
      onLandingsChange(selectedLandings.filter(l => l !== landing))
    } else {
      onLandingsChange([...selectedLandings, landing])
    }
    // Close mobile sheet after selection
    if (isMobile && onClose) {
      onClose()
    }
  }

  const clearAllLandings = () => {
    onLandingsChange([])
  }

  const sanDiegoLandings = landings.filter(l =>
    l.includes('Fisherman') ||
    l.includes('H&M') ||
    l.includes('Point Loma') ||
    l.includes('Seaforth')
  )

  const orangeCountyLandings = landings.filter(l =>
    l.includes('Dana') ||
    l.includes('Newport')
  )

  const losAngelesLandings = landings.filter(l =>
    l.includes('Long Beach') ||
    l.includes('San Pedro') ||
    l.includes('Redondo')
  )

  const channelIslandsLandings = landings.filter(l =>
    l.includes('Ventura') ||
    l.includes('Santa Barbara') ||
    l.includes('Oceanside')
  )

  // On mobile, don't show collapse functionality - Sheet handles visibility
  if (isCollapsed && !isMobile) {
    return (
      <aside className="w-12 border-r bg-background p-2 flex flex-col gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(false)}
          className="h-8 w-8"
        >
          <PanelLeft className="h-4 w-4" />
        </Button>
      </aside>
    )
  }

  return (
    <aside className={`${isMobile ? 'w-full' : 'w-72 border-r'} bg-background p-3 flex flex-col gap-2 overflow-y-auto`}>
      <Button
        variant={selectedLandings.length === 0 ? 'secondary' : 'ghost'}
        className="w-full justify-start h-8"
        onClick={clearAllLandings}
      >
        <MapPin className="mr-2 h-4 w-4" />
        All Landings
      </Button>

      <Separator />

      <div className="space-y-1">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground px-2">
          Pinned
        </h2>
        {Array.from(pinnedLandings).length === 0 ? (
          <div className="text-xs text-muted-foreground px-2">No pinned locations</div>
        ) : (
          <div className="space-y-1">
            {Array.from(pinnedLandings).map(landing => (
              <Button
                key={landing}
                variant={selectedLandings.includes(landing) ? 'secondary' : 'ghost'}
                className="w-full h-8 text-sm justify-between px-3 group"
                onClick={() => toggleLanding(landing)}
              >
                <span className="truncate">{landing}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 opacity-100"
                  onClick={(e) => togglePin(landing, e)}
                >
                  <Pin className="h-3.5 w-3.5 fill-current" />
                </Button>
              </Button>
            ))}
          </div>
        )}
      </div>

      <Separator />

      <Collapsible open={openSections.sanDiego} onOpenChange={() => toggleSection('sanDiego')}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-start px-2 h-8">
            <ChevronRight className={`mr-2 h-4 w-4 transition-transform ${openSections.sanDiego ? 'rotate-90' : ''}`} />
            <span className="text-xs font-semibold uppercase tracking-wide">San Diego</span>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-1 mt-1 pl-6">
          {sanDiegoLandings.map(landing => (
            <Button
              key={landing}
              variant={selectedLandings.includes(landing) ? 'secondary' : 'ghost'}
              className="w-full h-8 text-sm justify-between px-3 group font-normal"
              onClick={() => toggleLanding(landing)}
            >
              <span className="truncate">{landing}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => togglePin(landing, e)}
              >
                <Pin className={`h-3.5 w-3.5 ${pinnedLandings.has(landing) ? 'fill-current opacity-100' : ''}`} />
              </Button>
            </Button>
          ))}
        </CollapsibleContent>
      </Collapsible>

      <Collapsible open={openSections.orangeCounty} onOpenChange={() => toggleSection('orangeCounty')}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-start px-2 h-8">
            <ChevronRight className={`mr-2 h-4 w-4 transition-transform ${openSections.orangeCounty ? 'rotate-90' : ''}`} />
            <span className="text-xs font-semibold uppercase tracking-wide">Orange County</span>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-1 mt-1 pl-6">
          {orangeCountyLandings.length > 0 ? (
            orangeCountyLandings.map(landing => (
              <Button
                key={landing}
                variant={selectedLandings.includes(landing) ? 'secondary' : 'ghost'}
                className="w-full h-8 text-sm justify-between px-3 group font-normal"
                onClick={() => toggleLanding(landing)}
              >
                <span className="truncate">{landing}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => togglePin(landing, e)}
                >
                  <Pin className={`h-3.5 w-3.5 ${pinnedLandings.has(landing) ? 'fill-current opacity-100' : ''}`} />
                </Button>
              </Button>
            ))
          ) : (
            <div className="text-xs text-muted-foreground pl-2">No landings</div>
          )}
        </CollapsibleContent>
      </Collapsible>

      <Collapsible open={openSections.losAngeles} onOpenChange={() => toggleSection('losAngeles')}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-start px-2 h-8">
            <ChevronRight className={`mr-2 h-4 w-4 transition-transform ${openSections.losAngeles ? 'rotate-90' : ''}`} />
            <span className="text-xs font-semibold uppercase tracking-wide">Los Angeles</span>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-1 mt-1 pl-6">
          {losAngelesLandings.length > 0 ? (
            losAngelesLandings.map(landing => (
              <Button
                key={landing}
                variant={selectedLandings.includes(landing) ? 'secondary' : 'ghost'}
                className="w-full h-8 text-sm justify-between px-3 group font-normal"
                onClick={() => toggleLanding(landing)}
              >
                <span className="truncate">{landing}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => togglePin(landing, e)}
                >
                  <Pin className={`h-3.5 w-3.5 ${pinnedLandings.has(landing) ? 'fill-current opacity-100' : ''}`} />
                </Button>
              </Button>
            ))
          ) : (
            <div className="text-xs text-muted-foreground pl-2">No landings</div>
          )}
        </CollapsibleContent>
      </Collapsible>

      <Collapsible open={openSections.channelIslands} onOpenChange={() => toggleSection('channelIslands')}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-start px-2 h-8">
            <ChevronRight className={`mr-2 h-4 w-4 transition-transform ${openSections.channelIslands ? 'rotate-90' : ''}`} />
            <span className="text-xs font-semibold uppercase tracking-wide">Channel Islands</span>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-1 mt-1 pl-6">
          {channelIslandsLandings.length > 0 ? (
            channelIslandsLandings.map(landing => (
              <Button
                key={landing}
                variant={selectedLandings.includes(landing) ? 'secondary' : 'ghost'}
                className="w-full h-8 text-sm justify-between px-3 group font-normal"
                onClick={() => toggleLanding(landing)}
              >
                <span className="truncate">{landing}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => togglePin(landing, e)}
                >
                  <Pin className={`h-3.5 w-3.5 ${pinnedLandings.has(landing) ? 'fill-current opacity-100' : ''}`} />
                </Button>
              </Button>
            ))
          ) : (
            <div className="text-xs text-muted-foreground pl-2">No landings</div>
          )}
        </CollapsibleContent>
      </Collapsible>
    </aside>
  )
}
