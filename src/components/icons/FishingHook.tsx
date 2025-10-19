import React from 'react'

interface FishingHookProps {
  className?: string
}

export function FishingHook({ className }: FishingHookProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {/* Fishing hook path */}
      <path d="M12 3v6" />
      <path d="M12 9c-2.5 0-4.5 2-4.5 4.5s2 4.5 4.5 4.5 4.5-2 4.5-4.5" />
      <circle cx="12" cy="13.5" r="2.5" />
      <path d="M12 16v5" />
    </svg>
  )
}
