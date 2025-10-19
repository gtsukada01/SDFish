# Data Model: Southern California Offshore Analytics Table

## 1. Catch Record
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique identifier for the record (matches Supabase primary key). |
| `trip_date` | string (ISO 8601 date) | Yes | Calendar date of the offshore trip. |
| `boat` | string | Yes | Vessel name running the trip. |
| `landing` | string | Yes | Home landing/port for the trip. |
| `trip_duration_hours` | number | Yes | Duration of the trip in hours (decimal). |
| `angler_count` | number (integer ≥ 0) | Yes | Number of anglers onboard; blanks represented as `null` but surfaced as empty cell in UI. |
| `total_fish` | number (integer ≥ 0) | Yes | Total fish caught during trip. |
| `top_species` | string | Yes | Most frequently caught species for the trip. |
| `top_species_count` | number (integer ≥ 0) | Yes | Number of fish for the top species. |
| `species_breakdown` | array of objects | No | Additional species/catch counts (`{ species: string; count: number }`). |
| `weather_notes` | string | No | Optional notes on weather/ocean conditions. |
| `created_at` | string (ISO datetime) | Yes | Timestamp for data ingestion. |

**Blank Handling**: Any field flagged as required but absent in Supabase is returned as `null` and logged via telemetry; UI renders an empty cell.

## 2. Filter Criteria
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_date` | string (ISO date) | Yes | Default to 30 days prior to current date. |
| `end_date` | string (ISO date) | Yes | Default to current date. |
| `species` | array of strings | No | Multi-select species filter; empty array = all. |
| `landing` | string | No | Landing/port filter. |
| `boat` | string | No | Vessel filter. |
| `limit` | number | No | Progressive loading batch size (default 1000 when total rows > 6000). |
| `cursor` | string | No | Pagination cursor encoded by Supabase edge function. |

## 3. Summary Metrics
### Fleet Metrics
| Field | Type | Description |
|-------|------|-------------|
| `total_trips` | number | Total trips matching filters. |
| `total_fish` | number | Aggregate fish count across all boats. |
| `unique_boats` | number | Count of distinct boats represented. |
| `unique_species` | number | Count of distinct species represented. |

### Per-Boat Metrics
Array of objects `{ boat: string; trips: number; total_fish: number; top_species: string; top_species_count: number }`.

### Per-Species Metrics
Array of objects `{ species: string; total_fish: number; boats: number }`.

## 4. Data Refresh Status
| Field | Type | Description |
|-------|------|-------------|
| `last_synced_at` | string (ISO datetime) | Timestamp of last successful Supabase sync. |
| `status` | string enum (`"ok"`, `"degraded"`, `"error"`) | Current health of data pipeline. |
| `message` | string | Optional human-readable status detail. |

## 5. Telemetry Events
| Event | Payload |
|-------|---------|
| `fetch_start` | `{ endpoint: "catch" \| "metrics" \| "status", filters: FilterCriteria, timestamp: ISO }` |
| `fetch_success` | `{ endpoint, rows_returned?: number, duration_ms: number, timestamp: ISO }` |
| `fetch_error` | `{ endpoint, error_code: string, message: string, duration_ms?: number, timestamp: ISO }` |
| `blank_field_detected` | `{ record_id: string, fields: string[], timestamp: ISO }` |

## 6. Contract Overview
| Endpoint | Path | Method | Response Schema |
|----------|------|--------|-----------------|
| Catch Table | `functions/v1/offshore-catch` | GET | `contracts/catch-table.schema.json` |
| Summary Metrics | `functions/v1/offshore-metrics` | GET | `contracts/summary-metrics.schema.json` |
| Data Status | `functions/v1/offshore-status` | GET | `contracts/status.schema.json` |

Each response includes a `filters_applied` object matching the filter criteria structure, aiding replay/debugging.

## 7. Progressive Loading Protocol
- If `total_rows <= 6000`: return single page with full dataset.
- If `total_rows > 6000`: return first `limit` rows plus `cursor`; client requests additional pages while virtualization renders incremental rows.
- Responses include `next_cursor` (string|null). Empty indicates final batch.

## 8. Constraints & Validation Rules
- `trip_date` must be within the last 36 months; requests outside range return `400` with validation error.
- `end_date` must be ≥ `start_date` and difference ≤ 36 months.
- `species` values must belong to controlled vocabulary defined in Supabase `species` table.
- `top_species_count` cannot exceed `total_fish`.
- For summary metrics, totals must align: `sum(per_boat.total_fish) == total_fish` and `sum(per_species.total_fish) == total_fish`.

This data model feeds Spec Kit contract generation and TypeScript artifacts for downstream implementation.
