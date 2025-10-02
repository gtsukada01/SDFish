// AUTO-GENERATED - DO NOT EDIT BY HAND
// Generated from specs/001-offshore-analytics-table/contracts/*.mock.json
// Run: npm run generate:types

import {
  CatchTableResponse,
  StatusResponse,
  SummaryMetricsResponse,
} from './types.js';

export const mockCatchTableResponse: CatchTableResponse = {
  data: [
    {
      id: "8f6ec7c0-0b18-4a27-9c89-0e0cd258a8c9",
      trip_date: "2025-09-01",
      boat: "Pacific Pioneer",
      landing: "San Diego",
      trip_duration_hours: 24,
      angler_count: 25,
      total_fish: 250,
      top_species: "Bluefin Tuna",
      top_species_count: 140,
      species_breakdown: [
        {
          species: "Bluefin Tuna",
          count: 140
        },
        {
          species: "Yellowtail",
          count: 60
        },
        {
          species: "Bonito",
          count: 50
        }
      ],
      weather_notes: "Calm seas, light wind",
      created_at: "2025-09-01T12:30:00Z"
    },
    {
      id: "17acb879-4a38-4c61-ae29-0874a16cf62f",
      trip_date: "2025-09-02",
      boat: "Liberty",
      landing: "Point Loma",
      trip_duration_hours: 18,
      angler_count: null,
      total_fish: 180,
      top_species: "Yellowfin Tuna",
      top_species_count: 110,
      species_breakdown: [
        {
          species: "Yellowfin Tuna",
          count: 110
        },
        {
          species: "Skipjack",
          count: 40
        },
        {
          species: "Dorados",
          count: 30
        }
      ],
      weather_notes: null,
      created_at: "2025-09-02T08:25:00Z"
    }
  ],
  pagination: {
    total_rows: 8200,
    returned_rows: 1000,
    limit: 1000,
    next_cursor: "eyJvZmZzZXQiOjEwMDB9"
  },
  filters_applied: {
    start_date: "2025-08-28",
    end_date: "2025-09-27",
    species: [
      "Bluefin Tuna",
      "Yellowfin Tuna"
    ],
    landing: null,
    boat: null
  },
  last_synced_at: "2025-09-27T09:45:00Z"
} as const;

export const mockStatusResponse: StatusResponse = {
  status: "ok",
  last_synced_at: "2025-09-27T09:45:00Z",
  message: "Live feed updated within the last hour",
  incident_id: null
} as const;

export const mockSummaryMetricsResponse: SummaryMetricsResponse = {
  fleet: {
    total_trips: 220,
    total_fish: 18750,
    unique_boats: 5,
    unique_species: 4
  },
  per_boat: [
    {
      boat: "Pacific Pioneer",
      trips: 48,
      total_fish: 4500,
      top_species: "Bluefin Tuna",
      top_species_count: 2800
    },
    {
      boat: "Liberty",
      trips: 44,
      total_fish: 3750,
      top_species: "Yellowfin Tuna",
      top_species_count: 2100
    },
    {
      boat: "Polaris Supreme",
      trips: 42,
      total_fish: 3300,
      top_species: "Bluefin Tuna",
      top_species_count: 1850
    },
    {
      boat: "American Angler",
      trips: 40,
      total_fish: 3150,
      top_species: "Yellowtail",
      top_species_count: 1700
    },
    {
      boat: "Ocean Odyssey",
      trips: 46,
      total_fish: 4050,
      top_species: "Dorado",
      top_species_count: 1800
    }
  ],
  per_species: [
    {
      species: "Bluefin Tuna",
      total_fish: 6000,
      boats: 4
    },
    {
      species: "Yellowfin Tuna",
      total_fish: 5000,
      boats: 3
    },
    {
      species: "Yellowtail",
      total_fish: 4500,
      boats: 3
    },
    {
      species: "Dorado",
      total_fish: 3250,
      boats: 2
    }
  ],
  filters_applied: {
    start_date: "2025-08-28",
    end_date: "2025-09-27",
    species: [
      "Bluefin Tuna",
      "Yellowfin Tuna"
    ],
    landing: null,
    boat: null
  },
  last_synced_at: "2025-09-27T09:45:00Z"
} as const;
