import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Normalize species name for display grouping
 * Removes weight qualifiers and standardizes naming
 * Examples:
 * - "bluefin tuna (up to 50 pounds)" → "Bluefin Tuna"
 * - "bluefin tuna (up to 100 pounds)" → "Bluefin Tuna"
 * - "vermillion rockfish" → "Vermilion Rockfish"
 * - "vermilion rockfish" → "Vermilion Rockfish"
 */
export function normalizeSpeciesName(species: string): string {
  if (!species) return species

  // Remove "(up to XXX pounds)" patterns (handles both integers and decimals like 6.5)
  let normalized = species.replace(/\s*\(up to [\d.]+\s*pounds?\)/i, '').trim()

  // Fix common spelling variants and incomplete names (case-insensitive)
  const spellingFixes: Record<string, string> = {
    'vermillion rockfish': 'vermilion rockfish',
    'vermillion': 'vermilion',
    'blacksmith': 'blacksmith perch',
    'california yellowtail': 'yellowtail',
    'salmon grouper': 'bocaccio'
  }

  const lowerNormalized = normalized.toLowerCase()
  for (const [variant, correct] of Object.entries(spellingFixes)) {
    if (lowerNormalized === variant) {
      normalized = correct
      break
    }
  }

  // Capitalize first letter of each word for consistent display
  normalized = normalized
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')

  return normalized
}

/**
 * Group species by normalized names and create mapping
 * Input: ["bluefin tuna (up to 50 pounds)", "bluefin tuna (up to 100 pounds)", "yellowtail"]
 * Output: {
 *   normalizedNames: ["bluefin tuna", "yellowtail"],
 *   variantMap: Map {
 *     "bluefin tuna" => ["bluefin tuna (up to 50 pounds)", "bluefin tuna (up to 100 pounds)"],
 *     "yellowtail" => ["yellowtail"]
 *   }
 * }
 */
export function groupSpeciesByNormalizedName(allSpecies: string[]): {
  normalizedNames: string[]
  variantMap: Map<string, string[]>
} {
  const variantMap = new Map<string, string[]>()

  allSpecies.forEach(species => {
    const normalized = normalizeSpeciesName(species)
    if (!variantMap.has(normalized)) {
      variantMap.set(normalized, [])
    }
    variantMap.get(normalized)!.push(species)
  })

  const result = {
    normalizedNames: Array.from(variantMap.keys()).sort(),
    variantMap
  }

  return result
}

/**
 * Calculate Year-over-Year percentage change
 * @param current - Current year value (e.g., 2025)
 * @param previous - Previous year value (e.g., 2024)
 * @returns Percentage change (e.g., 23 for +23%)
 */
export function calculateYOY(current: number, previous: number): number | null {
  if (previous === 0 || !previous) return null
  return Math.round(((current - previous) / previous) * 100)
}

/**
 * Format YOY change for display
 * @param current - Current year value
 * @param previous - Previous year value
 * @param compact - Use compact format (K/M abbreviations) for mobile
 * @returns Object with formatted display values
 */
export function formatYOYChange(current: number, previous: number, compact = false): {
  absolute: number
  percentage: number | null
  direction: 'up' | 'down' | 'neutral'
  displayText: string
  displayTextCompact: string
} {
  const absolute = current - previous
  const percentage = calculateYOY(current, previous)

  const direction = absolute > 0 ? 'up' : absolute < 0 ? 'down' : 'neutral'

  const sign = absolute > 0 ? '+' : ''

  // Percentage-only format (industry best practice)
  const displayText = percentage !== null ? `${sign}${percentage}% YOY` : `${sign}${absolute} YOY`
  const displayTextCompact = displayText // Same format for both desktop and mobile

  return {
    absolute,
    percentage,
    direction,
    displayText,
    displayTextCompact
  }
}
