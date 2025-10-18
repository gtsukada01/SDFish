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
