import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Normalize species name for display grouping
 * Removes weight qualifiers and standardizes naming
 * Examples:
 * - "bluefin tuna (up to 50 pounds)" → "bluefin tuna"
 * - "bluefin tuna (up to 100 pounds)" → "bluefin tuna"
 * - "calico bass (up to 6.5 pounds)" → "calico bass"
 */
export function normalizeSpeciesName(species: string): string {
  if (!species) return species

  // Remove "(up to XXX pounds)" patterns (handles both integers and decimals like 6.5)
  const withoutWeight = species.replace(/\s*\(up to [\d.]+\s*pounds?\)/i, '').trim()

  return withoutWeight
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
  const percentageText = percentage !== null ? ` (${sign}${percentage}%)` : ''

  // Full format for desktop
  const displayText = `${sign}${absolute.toLocaleString()}${percentageText} YOY`

  // Compact format for mobile (percentage only for brevity)
  const displayTextCompact = percentage !== null ? `${sign}${percentage}% YOY` : `${sign}${absolute} YOY`

  return {
    absolute,
    percentage,
    direction,
    displayText,
    displayTextCompact
  }
}
