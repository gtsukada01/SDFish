import { test, expect } from "@playwright/test";
import {
  API_BASE_URL,
  BASE_METRICS,
  EMPTY_METRICS,
  FILTERED_METRICS,
  buildCatchResponse,
  fulfillJson,
} from "./support/mock-fixtures";

test.describe("desktop table experience", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(({ baseUrl }) => {
      (window as any).FISH_USE_MOCKS = false;
      (window as any).FISH_API_BASE_URL = baseUrl;
    }, { baseUrl: API_BASE_URL });
  });

  test("renders catch records and summary metrics", async ({ page }) => {
    await page.route("**/offshore-catch**", (route) => fulfillJson(route, buildCatchResponse({ nextCursor: "cursor-1", totalRows: 2000 })));
    await page.route("**/offshore-metrics**", (route) => fulfillJson(route, BASE_METRICS));

    await page.goto("/");

    const rows = page.locator("table.catch-table tbody tr");
    await expect(rows).toHaveCount(2);
    await expect(page.locator(".summary-grid .summary-card")).toHaveCount(4);
    await expect(page.locator(".summary-card__value").first()).toContainText("220");
    await expect(rows.first()).toContainText("Pacific Pioneer");
  });

  test("applies species filter and refreshes data", async ({ page }) => {
    const baselineCatch = buildCatchResponse({ nextCursor: "cursor-1", totalRows: 2000 });
    const filteredCatch = buildCatchResponse({
      species: "Yellowtail",
      nextCursor: null,
      totalRows: 1,
      data: [{ boat: "Yellowtail Express", topSpecies: "Yellowtail" }],
    });

    await page.route("**/offshore-catch**", (route) => {
      const url = new URL(route.request().url());
      const species = url.searchParams.getAll("species");
      if (species.includes("Yellowtail")) {
        return fulfillJson(route, filteredCatch);
      }
      return fulfillJson(route, baselineCatch);
    });

    await page.route("**/offshore-metrics**", (route) => {
      const url = new URL(route.request().url());
      const species = url.searchParams.getAll("species");
      if (species.includes("Yellowtail")) {
        return fulfillJson(route, FILTERED_METRICS);
      }
      return fulfillJson(route, BASE_METRICS);
    });

    await page.goto("/");
    await expect(page.locator("table.catch-table tbody tr")).toHaveCount(2);

    const filteredPromise = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("species=Yellowtail"),
    );

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: "Yellowtail" } }));
    });

    await filteredPromise;

    const rows = page.locator("table.catch-table tbody tr");
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText("Yellowtail Express");
    await expect(page.locator("[data-load-more]")).toBeDisabled();
  });

  test("shows empty state when filters return no records", async ({ page }) => {
    const baselineCatch = buildCatchResponse({ nextCursor: null });
    const emptyCatch = {
      ...buildCatchResponse({ species: "Ghost Fish", nextCursor: null, totalRows: 0, data: [] }),
      data: [],
      pagination: { total_rows: 0, returned_rows: 0, limit: 1000, next_cursor: null },
    } as const;

    await page.route("**/offshore-catch**", (route) => {
      const url = new URL(route.request().url());
      if (url.searchParams.getAll("species").includes("Ghost Fish")) {
        return fulfillJson(route, emptyCatch);
      }
      return fulfillJson(route, baselineCatch);
    });

    await page.route("**/offshore-metrics**", (route) => {
      const url = new URL(route.request().url());
      if (url.searchParams.getAll("species").includes("Ghost Fish")) {
        return fulfillJson(route, EMPTY_METRICS);
      }
      return fulfillJson(route, BASE_METRICS);
    });

    await page.goto("/");
    await expect(page.locator("table.catch-table tbody tr")).toHaveCount(2);

    const emptyPromise = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("Ghost+Fish"),
    );

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: "Ghost Fish" } }));
    });

    await emptyPromise;

    const emptyState = page.locator(".state--empty");
    await expect(emptyState).toHaveText(/No results/i);
    await expect(page.locator("table.catch-table")).toHaveCount(0);
  });

  test("loads additional pages when progressive control clicked", async ({ page }) => {
    const firstPage = buildCatchResponse({
      nextCursor: "cursor-1",
      totalRows: 3,
      data: [
        { boat: "Pacific Pioneer", topSpecies: "Bluefin Tuna" },
        { boat: "Liberty", topSpecies: "Yellowfin Tuna" },
      ],
    });

    const secondPage = buildCatchResponse({
      nextCursor: null,
      totalRows: 3,
      data: [{ boat: "Ocean Odyssey", topSpecies: "Dorado" }],
    });

    let catchCalls = 0;
    await page.route("**/offshore-catch**", (route) => {
      catchCalls += 1;
      const url = new URL(route.request().url());
      if (url.searchParams.get("cursor") === "cursor-1") {
        return fulfillJson(route, secondPage);
      }
      return fulfillJson(route, firstPage);
    });

    await page.route("**/offshore-metrics**", (route) => fulfillJson(route, BASE_METRICS));

    await page.goto("/");

    const loadMore = page.locator("[data-load-more]");
    await expect(loadMore).toHaveText(/Load more results/i);
    await expect(page.locator("table.catch-table tbody tr")).toHaveCount(2);

    const nextPagePromise = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("cursor=cursor-1"),
    );

    await loadMore.click();
    await nextPagePromise;

    await expect(page.locator("table.catch-table tbody tr")).toHaveCount(3);
    await expect(loadMore).toHaveText(/All results loaded/i);
    await expect(loadMore).toBeDisabled();
    expect(catchCalls).toBeGreaterThanOrEqual(2);
  });
});
