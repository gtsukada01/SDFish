import type { Route } from "@playwright/test";

export const API_BASE_URL = "https://tests.invalid";

export interface CatchFixtureOptions {
  nextCursor?: string | null;
  species?: string;
  data?: Array<{ boat: string; topSpecies?: string }>;
  totalRows?: number;
}

export function buildCatchResponse({
  nextCursor = null,
  species,
  totalRows = 2,
  data = [
    { boat: "Pacific Pioneer", topSpecies: "Bluefin Tuna" },
    { boat: "Liberty", topSpecies: "Yellowfin Tuna" },
  ],
}: CatchFixtureOptions = {}) {
  const records = data.map((entry, index) => ({
    id: `record-${species ?? "all"}-${index}`,
    trip_date: "2025-09-15",
    boat: entry.boat,
    landing: "San Diego",
    trip_duration_hours: 24,
    angler_count: 20,
    total_fish: 150 + index * 10,
    top_species: entry.topSpecies ?? "Yellowtail",
    top_species_count: 75 + index * 5,
    species_breakdown: [
      { species: entry.topSpecies ?? "Yellowtail", count: 75 + index * 5 },
    ],
    weather_notes: null,
    created_at: "2025-09-15T08:00:00Z",
  }));

  return {
    data: records,
    pagination: {
      total_rows: totalRows,
      returned_rows: records.length,
      limit: 1000,
      next_cursor: nextCursor ?? null,
    },
    filters_applied: {
      start_date: "2025-08-01",
      end_date: "2025-09-30",
      species: species ? [species] : [],
      landing: null,
      boat: null,
    },
    last_synced_at: "2025-09-30T12:00:00Z",
  } as const;
}

export const BASE_METRICS = {
  fleet: {
    total_trips: 220,
    total_fish: 18_750,
    unique_boats: 5,
    unique_species: 4,
  },
  per_boat: [
    { boat: "Pacific Pioneer", trips: 48, total_fish: 4_500, top_species: "Bluefin Tuna", top_species_count: 2_800 },
    { boat: "Liberty", trips: 44, total_fish: 3_750, top_species: "Yellowfin Tuna", top_species_count: 2_100 },
    { boat: "Polaris Supreme", trips: 42, total_fish: 3_300, top_species: "Bluefin Tuna", top_species_count: 1_850 },
    { boat: "American Angler", trips: 40, total_fish: 3_150, top_species: "Yellowtail", top_species_count: 1_700 },
    { boat: "Ocean Odyssey", trips: 46, total_fish: 4_050, top_species: "Dorado", top_species_count: 1_800 },
  ],
  per_species: [
    { species: "Bluefin Tuna", total_fish: 6_000, boats: 4 },
    { species: "Yellowfin Tuna", total_fish: 5_000, boats: 3 },
    { species: "Yellowtail", total_fish: 4_500, boats: 3 },
    { species: "Dorado", total_fish: 3_250, boats: 2 },
  ],
  filters_applied: {
    start_date: "2025-08-01",
    end_date: "2025-09-30",
    species: [],
    landing: null,
    boat: null,
  },
  last_synced_at: "2025-09-30T12:00:00Z",
} as const;

export const FILTERED_METRICS = {
  fleet: {
    total_trips: 12,
    total_fish: 640,
    unique_boats: 1,
    unique_species: 1,
  },
  per_boat: [
    {
      boat: "Yellowtail Express",
      trips: 12,
      total_fish: 640,
      top_species: "Yellowtail",
      top_species_count: 320,
    },
  ],
  per_species: [{ species: "Yellowtail", total_fish: 640, boats: 1 }],
  filters_applied: {
    start_date: "2025-08-01",
    end_date: "2025-09-30",
    species: ["Yellowtail"],
    landing: null,
    boat: null,
  },
  last_synced_at: "2025-09-30T12:00:00Z",
} as const;

export const EMPTY_METRICS = {
  fleet: {
    total_trips: 0,
    total_fish: 0,
    unique_boats: 0,
    unique_species: 0,
  },
  per_boat: [],
  per_species: [],
  filters_applied: {
    start_date: "2025-08-01",
    end_date: "2025-09-30",
    species: ["Ghost Fish"],
    landing: null,
    boat: null,
  },
  last_synced_at: "2025-09-30T12:00:00Z",
} as const;

export async function fulfillJson(route: Route, payload: unknown) {
  await route.fulfill({
    status: 200,
    body: JSON.stringify(payload),
    headers: { "content-type": "application/json" },
  });
}
