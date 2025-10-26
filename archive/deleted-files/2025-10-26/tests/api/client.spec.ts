import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createApiClient } from "../../scripts/api/client";
import type { CatchTableResponse, SummaryMetricsResponse } from "../../scripts/api/types";

const BASE_CATCH_RESPONSE: CatchTableResponse = {
  data: [
    {
      id: "record-1",
      trip_date: "2025-09-01",
      boat: "Pacific Pioneer",
      landing: "San Diego",
      trip_duration_hours: 24,
      angler_count: 25,
      total_fish: 250,
      top_species: "Yellowtail",
      top_species_count: 140,
      created_at: "2025-09-01T12:30:00Z",
    },
  ],
  pagination: {
    total_rows: 1,
    returned_rows: 1,
    limit: 1000,
    next_cursor: null,
  },
  filters_applied: {
    start_date: "2025-09-01",
    end_date: "2025-09-30",
  },
  last_synced_at: "2025-09-30T09:45:00Z",
};

const BASE_METRICS_RESPONSE: SummaryMetricsResponse = {
  fleet: {
    total_trips: 48,
    total_fish: 4500,
    unique_boats: 1,
    unique_species: 1,
  },
  per_boat: [
    {
      boat: "Pacific Pioneer",
      trips: 48,
      total_fish: 4500,
      top_species: "Bluefin Tuna",
      top_species_count: 2800,
    },
  ],
  per_species: [
    {
      species: "Bluefin Tuna",
      total_fish: 4500,
      boats: 1,
    },
  ],
  filters_applied: {
    start_date: "2025-09-01",
    end_date: "2025-09-30",
  },
  last_synced_at: "2025-09-30T09:45:00Z",
};

const originalFetch = globalThis.fetch;

describe("createApiClient", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    globalThis.fetch = originalFetch;
  });

  it("builds Supabase URLs and headers when loading catch data", async () => {
    const responseBody = structuredClone(BASE_CATCH_RESPONSE);
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(responseBody), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const client = createApiClient({
      baseUrl: "https://example.supabase.co/functions/v1",
      useMocks: false,
      anonKey: "anon-key",
    });

    const result = await client.loadCatchTable({
      filters: {
        start_date: "2025-09-01",
        end_date: "2025-09-30",
        species: ["Yellowtail", "Bluefin Tuna"],
        limit: 1000,
      },
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [urlRaw, init] = fetchMock.mock.calls[0];
    const url = new URL(urlRaw as string);
    expect(url.pathname).toBe("/functions/v1/offshore-catch");
    expect(url.searchParams.getAll("species")).toEqual([
      "Yellowtail",
      "Bluefin Tuna",
    ]);
    expect(url.searchParams.get("limit")).toBe("1000");

    expect(init?.headers).toMatchObject({
      Accept: "application/json",
      apikey: "anon-key",
      Authorization: "Bearer anon-key",
    });

    expect(result.pagination.next_cursor).toBeNull();
    expect(result.data).toHaveLength(1);
  });

  it("streams paginated catch responses sequentially", async () => {
    const firstPage: CatchTableResponse = {
      ...structuredClone(BASE_CATCH_RESPONSE),
      pagination: {
        total_rows: 2,
        returned_rows: 1,
        limit: 1000,
        next_cursor: "cursor-1",
      },
    };
    const secondPage: CatchTableResponse = {
      ...structuredClone(BASE_CATCH_RESPONSE),
      data: [
        {
          ...structuredClone(BASE_CATCH_RESPONSE.data[0]),
          id: "record-2",
          boat: "Liberty",
        },
      ],
      pagination: {
        total_rows: 2,
        returned_rows: 1,
        limit: 1000,
        next_cursor: null,
      },
    };

    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify(firstPage), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(secondPage), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

    const client = createApiClient({
      baseUrl: "https://example.supabase.co/functions/v1",
      useMocks: false,
    });

    const pages: CatchTableResponse[] = [];
    for await (const page of client.streamCatchTable({
      filters: { start_date: "2025-09-01", end_date: "2025-09-30" },
    })) {
      pages.push(page);
    }

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(pages).toHaveLength(2);
    const secondCallUrl = new URL(fetchMock.mock.calls[1][0] as string);
    expect(secondCallUrl.searchParams.get("cursor")).toBe("cursor-1");
    expect(pages[1].data[0].boat).toBe("Liberty");
  });

  it("returns empty data when mocks are paginated", async () => {
    const client = createApiClient({ useMocks: true });

    const first = await client.loadCatchTable({});
    expect(first.data.length).toBeGreaterThan(0);
    expect(first.pagination.next_cursor).not.toBeNull();

    const next = await client.loadCatchTable({ filters: { cursor: "cursor-1" } });
    expect(next.data).toHaveLength(0);
    expect(next.pagination.next_cursor).toBeNull();
  });

  it("omits cursor and limit when loading metrics", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(BASE_METRICS_RESPONSE), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const client = createApiClient({
      baseUrl: "https://example.supabase.co/functions/v1",
      useMocks: false,
    });

    await client.loadSummaryMetrics({
      filters: {
        start_date: "2025-09-01",
        end_date: "2025-09-30",
        cursor: "cursor-1",
        limit: 1000,
      },
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const url = new URL(fetchMock.mock.calls[0][0] as string);
    expect(url.pathname).toBe("/functions/v1/offshore-metrics");
    expect(url.searchParams.has("cursor")).toBe(false);
    expect(url.searchParams.has("limit")).toBe(false);
  });
});
