import {
  CatchTableResponse,
  SummaryMetricsResponse,
  StatusResponse,
  Filters,
} from "./types";
import {
  emitTelemetry,
  logBlankFields,
  detectBlankFields,
  now,
} from "./instrumentation";
import {
  mockCatchTableResponse,
  mockSummaryMetricsResponse,
  mockStatusResponse,
} from "./mocks";
import {
  validateCatchTableResponse,
  validateSummaryMetricsResponse,
  validateStatusResponse,
} from "./validators";

export interface ApiClientConfig {
  baseUrl?: string;
  useMocks?: boolean;
  anonKey?: string;
}

export interface FetchOptions {
  filters?: Partial<Filters>;
  signal?: AbortSignal;
}

const DEFAULT_BASE_URL = "/api";
const DATA_QUALITY_FIELDS = [
  "boat",
  "landing",
  "angler_count",
  "top_species",
] as const;

export function createApiClient(config: ApiClientConfig = {}) {
  const baseUrl = trimTrailingSlash(config.baseUrl ?? DEFAULT_BASE_URL);
  const useMocks = config.useMocks ?? false;
  const baseHeaders = buildHeaders(config.anonKey);

  async function fetchCatchPage(
    filters: Partial<Filters>,
    signal?: AbortSignal,
  ): Promise<CatchTableResponse> {
    const sanitized = normalizeFilters(filters);
    const endpoint = "catch" as const;
    const startedAt = performance.now();

    await emitTelemetry({
      event: "fetch_start",
      endpoint,
      filters: sanitized,
      timestamp: now(),
    });

    try {
      let payload: CatchTableResponse;

      if (useMocks) {
        payload = clone(mockCatchTableResponse);
        if (sanitized.cursor) {
          payload.data = [];
          payload.pagination = {
            ...payload.pagination,
            returned_rows: 0,
            next_cursor: null,
          };
        } else {
          payload.pagination = {
            ...payload.pagination,
            returned_rows: payload.data.length,
          };
        }
      } else {
        const url = buildEndpointUrl(baseUrl, "offshore-catch", sanitized);
        payload = await fetchJson<CatchTableResponse>(url, {
          signal,
          headers: { ...baseHeaders },
        });
      }

      validateCatchTableResponse(payload);

      for (const record of payload.data) {
        const blanks = detectBlankFields(
          record as unknown as Record<string, unknown>,
          DATA_QUALITY_FIELDS,
        );
        if (blanks.length > 0) {
          await logBlankFields(record.id, blanks);
        }
      }

      const duration = performance.now() - startedAt;
      await emitTelemetry({
        event: "fetch_success",
        endpoint,
        duration_ms: Math.round(duration),
        rows_returned: payload.data.length,
        timestamp: now(),
      });

      return payload;
    } catch (error) {
      const duration = performance.now() - startedAt;
      await emitTelemetry({
        event: "fetch_error",
        endpoint,
        duration_ms: Math.round(duration),
        error_code: error instanceof Error ? error.name : "unknown",
        message: error instanceof Error ? error.message : String(error),
        timestamp: now(),
      });
      throw error;
    }
  }

  async function loadCatchTable(options: FetchOptions = {}): Promise<CatchTableResponse> {
    return fetchCatchPage(options.filters ?? {}, options.signal);
  }

  async function* streamCatchTable(
    options: FetchOptions = {},
  ): AsyncGenerator<CatchTableResponse, void, unknown> {
    const baseFilters = normalizeFilters(options.filters ?? {});
    const initialCursor = baseFilters.cursor ?? null;
    if (initialCursor) {
      delete baseFilters.cursor;
    }

    const firstPage = await fetchCatchPage(
      initialCursor ? { ...baseFilters, cursor: initialCursor } : baseFilters,
      options.signal,
    );
    yield firstPage;

    if (useMocks) {
      return;
    }

    let cursor = firstPage.pagination.next_cursor;

    while (cursor) {
      const nextPage = await fetchCatchPage({ ...baseFilters, cursor }, options.signal);
      yield nextPage;
      cursor = nextPage.pagination.next_cursor;
    }
  }

  async function loadSummaryMetrics(
    options: FetchOptions = {},
  ): Promise<SummaryMetricsResponse> {
    const endpoint = "metrics" as const;
    const filters = normalizeFilters(options.filters ?? {});
    delete filters.cursor;
    delete filters.limit;

    const startedAt = performance.now();
    await emitTelemetry({
      event: "fetch_start",
      endpoint,
      filters,
      timestamp: now(),
    });

    try {
      let payload: SummaryMetricsResponse;

      if (useMocks) {
        payload = clone(mockSummaryMetricsResponse);
      } else {
        const url = buildEndpointUrl(baseUrl, "offshore-metrics", filters);
        payload = await fetchJson<SummaryMetricsResponse>(url, {
          signal: options.signal,
          headers: { ...baseHeaders },
        });
      }

      validateSummaryMetricsResponse(payload);

      const duration = performance.now() - startedAt;
      await emitTelemetry({
        event: "fetch_success",
        endpoint,
        duration_ms: Math.round(duration),
        rows_returned: payload.per_boat.length,
        timestamp: now(),
      });

      return payload;
    } catch (error) {
      const duration = performance.now() - startedAt;
      await emitTelemetry({
        event: "fetch_error",
        endpoint,
        duration_ms: Math.round(duration),
        error_code: error instanceof Error ? error.name : "unknown",
        message: error instanceof Error ? error.message : String(error),
        timestamp: now(),
      });
      throw error;
    }
  }

  async function loadStatus(options: FetchOptions = {}): Promise<StatusResponse> {
    const endpoint = "status" as const;
    const startedAt = performance.now();

    await emitTelemetry({
      event: "fetch_start",
      endpoint,
      filters: {},
      timestamp: now(),
    });

    try {
      let payload: StatusResponse;

      if (useMocks) {
        payload = clone(mockStatusResponse);
      } else {
        const url = buildEndpointUrl(baseUrl, "offshore-status", {});
        payload = await fetchJson<StatusResponse>(url, {
          signal: options.signal,
          headers: { ...baseHeaders },
        });
      }

      validateStatusResponse(payload);

      const duration = performance.now() - startedAt;
      await emitTelemetry({
        event: "fetch_success",
        endpoint,
        duration_ms: Math.round(duration),
        timestamp: now(),
      });

      return payload;
    } catch (error) {
      const duration = performance.now() - startedAt;
      await emitTelemetry({
        event: "fetch_error",
        endpoint,
        duration_ms: Math.round(duration),
        error_code: error instanceof Error ? error.name : "unknown",
        message: error instanceof Error ? error.message : String(error),
        timestamp: now(),
      });
      throw error;
    }
  }

  return {
    loadCatchTable,
    streamCatchTable,
    loadSummaryMetrics,
    loadStatus,
  };
}

function buildHeaders(anonKey?: string): Record<string, string> {
  if (!anonKey) {
    return { Accept: "application/json" };
  }

  return {
    Accept: "application/json",
    apikey: anonKey,
    Authorization: `Bearer ${anonKey}`,
  };
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);

  if (!response.ok) {
    let detail: string | undefined;
    try {
      detail = await response.text();
    } catch (error) {
      detail = undefined;
    }

    const message = detail && detail.length > 0 ? `: ${detail}` : "";
    const error = new Error(`Request failed with ${response.status} ${response.statusText}${message}`);
    error.name = `HTTP_${response.status}`;
    throw error;
  }

  return (await response.json()) as T;
}

function buildEndpointUrl(
  baseUrl: string,
  endpoint: string,
  filters: Partial<Filters>,
): string {
  const normalizedEndpoint = endpoint.replace(/^\/+/, "");
  const normalizedBase = trimTrailingSlash(baseUrl);
  const query = buildQuery(filters);
  if (normalizedBase.length === 0) {
    return `/${normalizedEndpoint}${query}`;
  }
  return `${normalizedBase}/${normalizedEndpoint}${query}`;
}

function buildQuery(filters: Partial<Filters>): string {
  const params = new URLSearchParams();

  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);

  if (Array.isArray(filters.species)) {
    for (const species of filters.species) {
      if (species) params.append("species", species);
    }
  }

  if (filters.landing) params.set("landing", filters.landing);
  if (filters.boat) params.set("boat", filters.boat);

  if (typeof filters.limit === "number" && Number.isFinite(filters.limit) && filters.limit > 0) {
    params.set("limit", String(filters.limit));
  }

  if (filters.cursor) params.set("cursor", filters.cursor);

  const query = params.toString();
  return query.length > 0 ? `?${query}` : "";
}

function normalizeFilters(filters: Partial<Filters>): Partial<Filters> {
  const normalized: Partial<Filters> = {};

  if (filters.start_date) normalized.start_date = filters.start_date;
  if (filters.end_date) normalized.end_date = filters.end_date;

  if (Array.isArray(filters.species) && filters.species.length > 0) {
    normalized.species = filters.species.filter(Boolean);
  }

  if (typeof filters.landing === "string" && filters.landing.length > 0) {
    normalized.landing = filters.landing;
  }

  if (typeof filters.boat === "string" && filters.boat.length > 0) {
    normalized.boat = filters.boat;
  }

  if (typeof filters.limit === "number" && Number.isFinite(filters.limit) && filters.limit > 0) {
    normalized.limit = filters.limit;
  }

  if (typeof filters.cursor === "string" && filters.cursor.length > 0) {
    normalized.cursor = filters.cursor;
  }

  return normalized;
}

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}
