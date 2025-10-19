// AUTO-GENERATED - DO NOT EDIT BY HAND
// Generated from specs/001-offshore-analytics-table/contracts/*.schema.json
// Run: npm run generate:types

export interface CatchTableResponse {
  data: CatchRecord[];
  pagination: {
    total_rows: number;
    returned_rows: number;
    limit: number;
    next_cursor: string | null;
  };
  filters_applied: Filters;
  last_synced_at: string;
}

export interface CatchRecord {
  id: string;
  trip_date: string;
  boat: string;
  landing: string;
  trip_duration_hours: number;
  angler_count: number | null;
  total_fish: number;
  top_species: string;
  top_species_count: number;
  species_breakdown?: {
    species: string;
    count: number;
  }[];
  weather_notes?: string | null;
  created_at: string;
}

export interface Filters {
  start_date: string;
  end_date: string;
  species?: string[];
  landing?: string | null;
  boat?: string | null;
  trip_duration?: string | null;
  limit?: number | null;
  cursor?: string | null;
}

export interface StatusResponse {
  status: StatusState;
  last_synced_at: string;
  message?: string | null;
  /**
   * Identifier for tracking related incident in ops tooling.
   */
  incident_id?: string | null;
}

export interface SummaryMetricsResponse {
  fleet: {
    total_trips: number;
    total_fish: number;
    unique_boats: number;
    unique_species: number;
  };
  per_boat: {
    boat: string;
    trips: number;
    total_fish: number;
    top_species: string;
    top_species_count: number;
  }[];
  per_species: {
    species: string;
    total_fish: number;
    boats: number;
  }[];
  moon_phase?: {
    phase_name: string;
    total_fish: number;
    trip_count: number;
    avg_fish_per_trip: number;
  }[];
  filters_applied: Filters;
  last_synced_at: string;
}

export type StatusState = "ok" | "degraded" | "error";
