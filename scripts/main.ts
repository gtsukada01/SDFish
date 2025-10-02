import { createApiClient } from "./api/client";
import { configureTelemetry } from "./api/instrumentation";
import { Filters, CatchRecord, SummaryMetricsResponse } from "./api/types";
import { setLoading, setError, setEmpty, clearState } from "./ui/states";
import { renderCatchTable, cleanupVirtualizer } from "./ui/table";
import { renderSummaryMetrics } from "./ui/metrics";
import { updateProgressiveControl } from "./ui/progressive";
import {
  createFiltersPanel,
  FILTER_CHANGE_EVENT,
  FilterChangeEvent,
  FilterChangeDetail,
  FiltersPanelController,
  FilterCollections,
} from "./ui/filters";

const DEFAULT_RANGE_DAYS = 30;
const FILTER_DEBOUNCE_MS = 300;
const TELEMETRY_ENDPOINT = (window as any).FISH_TELEMETRY_ENDPOINT ?? null;
const USE_MOCKS = (window as any).FISH_USE_MOCKS ?? true;
const SUPABASE_URL = stringOrNull((window as any).FISH_SUPABASE_URL);
const SUPABASE_ANON_KEY = stringOrNull((window as any).FISH_SUPABASE_ANON_KEY);
const API_BASE_URL = resolveApiBaseUrl({
  supabaseUrl: SUPABASE_URL,
  fallbackBase: stringOrNull((window as any).FISH_API_BASE_URL) ?? "/api",
});

interface AppState {
  filters: Filters;
  records: CatchRecord[];
  metrics: SummaryMetricsResponse | null;
  nextCursor: string | null;
  loading: boolean;
}

const state: AppState = {
  filters: createDefaultFilters(),
  records: [],
  metrics: null,
  nextCursor: null,
  loading: false,
};

const api = createApiClient({
  useMocks: USE_MOCKS,
  baseUrl: API_BASE_URL,
  anonKey: SUPABASE_ANON_KEY ?? undefined,
});

const tableSection = document.getElementById("recentTripsContainer") as HTMLElement | null;
const metricsSection = document.getElementById("statsGridContainer") as HTMLElement | null;
const filtersSection = document.getElementById("filtersMount") as HTMLElement | null;

const tableMount = document.createElement("div");
const progressiveMount = document.createElement("div");
progressiveMount.className = "progressive-control";

if (tableSection) {
  tableMount.id = "catchTableMount";
  tableSection.appendChild(tableMount);
  tableSection.appendChild(progressiveMount);
}

let filtersPanel: FiltersPanelController | null = null;
let filterCollections: FilterCollections = { landings: [], boats: [], species: [] };
let filterDebounceHandle: number | null = null;
let inflightController: AbortController | null = null;

if (filtersSection) {
  filtersPanel = createFiltersPanel(filtersSection, {
    initialFilters: state.filters,
    options: filterCollections,
  });

  filtersSection.addEventListener(FILTER_CHANGE_EVENT, (event) => {
    const custom = event as FilterChangeEvent;
    handleFilterChange(custom.detail);
  });
}

configureTelemetry(TELEMETRY_ENDPOINT ?? null);

document.addEventListener("DOMContentLoaded", () => {
  bootstrap();
});

document.addEventListener("mock-filter", (event) => {
  if (!filtersPanel) return;
  const custom = event as CustomEvent<{ species?: string | null }>;
  const speciesValue = custom.detail?.species ?? null;
  const next: Filters = {
    start_date: state.filters.start_date,
    end_date: state.filters.end_date,
  };

  if (speciesValue) {
    next.species = [speciesValue];
  }

  filtersPanel.setFilters(next, "user");
});

async function bootstrap() {
  if (!tableSection || !metricsSection) return;
  await refresh(state.filters, { skipTelemetry: true });
}

interface RefreshOptions {
  append?: boolean;
  skipTelemetry?: boolean;
}

async function refresh(filters: Filters, options: RefreshOptions = {}) {
  if (!options.append && inflightController) {
    inflightController.abort();
  }

  // Cleanup virtualizer on full refresh
  if (!options.append) {
    cleanupVirtualizer();
  }

  inflightController = new AbortController();
  const { signal } = inflightController;

  state.loading = true;
  if (!options.append && tableMount) {
    setLoading(tableMount);
  }
  if (metricsSection) {
    setLoading(metricsSection, "Loading summary metrics...");
  }

  try {
    const catchPromise = api.loadCatchTable({ filters, signal });
    const metricsPromise = options.append
      ? null
      : api.loadSummaryMetrics({ filters, signal });

    const catchResponse = await catchPromise;
    const metricsResponse = metricsPromise ? await metricsPromise : state.metrics;

    const records = options.append ? [...state.records, ...catchResponse.data] : catchResponse.data;
    state.records = records;
    state.metrics = metricsResponse ?? null;
    state.filters = { ...filters, cursor: undefined };
    state.nextCursor = catchResponse.pagination.next_cursor;

    updateFilterCollections(state.records, state.metrics);

    if (tableMount) {
      if (records.length === 0) {
        setEmpty(tableMount, "No results. Try adjusting filters.", {
          onRetry: () => {
            if (filtersPanel) {
              filtersPanel.setFilters(createDefaultFilters(), "user");
            }
          },
          onTelemetry: (event) => console.log("[Telemetry]", event),
        });
      } else {
        clearState(tableMount);
        renderCatchTable(tableMount, records);
      }
    }

    if (state.metrics && metricsSection) {
      clearState(metricsSection);
      renderSummaryMetrics(metricsSection, state.metrics);
    }

    updateProgressiveControl(progressiveMount, catchResponse, async (cursor) => {
      const nextFilters: Filters = {
        ...state.filters,
        cursor,
      };
      await refresh(nextFilters, { append: true });
      return Boolean(state.nextCursor);
    });
  } catch (error) {
    if (isAbortError(error)) {
      return;
    }
    console.error("Failed to load data", error);
    if (tableMount) {
      setError(tableMount, "Unable to load fishing data. Please try again later.", {
        onRetry: () => refresh(filters),
        onTelemetry: (event) => console.log("[Telemetry]", event),
      });
    }
    if (metricsSection) {
      setError(metricsSection, "Summary metrics unavailable.", {
        onRetry: () => refresh(filters),
        onTelemetry: (event) => console.log("[Telemetry]", event),
      });
    }
  } finally {
    state.loading = false;
    if (inflightController?.signal === signal) {
      inflightController = null;
    }
  }
}

function handleFilterChange({ filters, reason }: FilterChangeDetail) {
  const nextFilters = formatFiltersForRefresh(filters);

  if (filterDebounceHandle !== null) {
    window.clearTimeout(filterDebounceHandle);
  }

  filterDebounceHandle = window.setTimeout(() => {
    filterDebounceHandle = null;
    void refresh(nextFilters);
  }, FILTER_DEBOUNCE_MS);
}

function updateFilterCollections(records: CatchRecord[], metrics: SummaryMetricsResponse | null) {
  if (!filtersPanel) return;

  filterCollections = deriveFilterCollections(records, metrics);
  filtersPanel.setOptions(filterCollections);
  filtersPanel.setFilters(state.filters);
}

function createDefaultFilters(): Filters {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - DEFAULT_RANGE_DAYS);

  return {
    start_date: start.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10),
  };
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function resolveApiBaseUrl({
  supabaseUrl,
  fallbackBase,
}: {
  supabaseUrl: string | null;
  fallbackBase: string;
}): string {
  if (supabaseUrl) {
    const trimmed = supabaseUrl.replace(/\/+$/, "");
    return /\/functions\/v1$/i.test(trimmed)
      ? trimmed
      : `${trimmed}/functions/v1`;
  }
  return fallbackBase;
}

function formatFiltersForRefresh(detail: Filters): Filters {
  const next: Filters = {
    start_date: detail.start_date,
    end_date: detail.end_date,
  };

  if (Array.isArray(detail.species) && detail.species.length > 0) {
    next.species = [...detail.species];
  }

  if (typeof detail.landing === "string") {
    next.landing = detail.landing;
  }

  if (typeof detail.boat === "string") {
    next.boat = detail.boat;
  }

  if (typeof state.filters.limit === "number") {
    next.limit = state.filters.limit;
  }

  return next;
}

function deriveFilterCollections(
  records: CatchRecord[],
  metrics: SummaryMetricsResponse | null,
): FilterCollections {
  const landings = new Set<string>();
  const boats = new Set<string>();
  const species = new Set<string>();

  for (const record of records) {
    if (record.landing) {
      landings.add(record.landing);
    }
    if (record.boat) {
      boats.add(record.boat);
    }
    if (record.top_species) {
      species.add(record.top_species);
    }
    if (record.species_breakdown) {
      for (const entry of record.species_breakdown) {
        if (entry?.species) {
          species.add(entry.species);
        }
      }
    }
  }

  if (metrics) {
    for (const boatMetric of metrics.per_boat) {
      if (boatMetric.boat) {
        boats.add(boatMetric.boat);
      }
      if (boatMetric.top_species) {
        species.add(boatMetric.top_species);
      }
    }
    for (const speciesMetric of metrics.per_species) {
      if (speciesMetric.species) {
        species.add(speciesMetric.species);
      }
    }
  }

  return {
    landings: Array.from(landings).sort(localeSorter),
    boats: Array.from(boats).sort(localeSorter),
    species: Array.from(species).sort(localeSorter),
  };
}

function localeSorter(a: string, b: string): number {
  return a.localeCompare(b);
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}
