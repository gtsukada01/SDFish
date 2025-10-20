import { devices, expect, test } from "@playwright/test";
import {
  API_BASE_URL,
  BASE_METRICS,
  EMPTY_METRICS,
  FILTERED_METRICS,
  buildCatchResponse,
  fulfillJson,
} from "./support/mock-fixtures";

const baseDevice = devices["iPhone 14 Pro Max"];

const iphone17 = {
  viewport: { width: 430, height: 932 },
  screen: { width: 430, height: 932 },
  userAgent:
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
  deviceScaleFactor: baseDevice.deviceScaleFactor,
  isMobile: true,
  hasTouch: true,
} as const;

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

test.describe.configure({ mode: "parallel" });

test.describe("iphone 17 responsive layout", () => {
  test.use(iphone17);

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(({ baseUrl }) => {
      (window as any).FISH_USE_MOCKS = false;
      (window as any).FISH_API_BASE_URL = baseUrl;
    }, { baseUrl: API_BASE_URL });
  });

  test("renders catch records and summary metrics with mobile layout", async ({ page }) => {
    await page.route("**/offshore-catch**", (route) =>
      fulfillJson(route, buildCatchResponse({ nextCursor: "cursor-1", totalRows: 2000 })),
    );
    await page.route("**/offshore-metrics**", (route) => fulfillJson(route, BASE_METRICS));

    await page.goto("/");

    await expect(page.locator(".sidebar")).toBeHidden();

    const columns = await page.locator(".app-layout").evaluate((node) =>
      window.getComputedStyle(node).gridTemplateColumns,
    );
    const columnParts = columns.trim().split(/\s+/);
    expect(columnParts.length).toBe(1);

    const coarsePointer = await page.evaluate(() => window.matchMedia("(pointer: coarse)").matches);
    expect(coarsePointer).toBe(true);

    const rows = page.locator("table.catch-table tbody tr");
    await expect(rows).toHaveCount(2);
    await expect(rows.first()).toContainText("Pacific Pioneer");
    await expect(page.locator(".summary-grid .summary-card")).toHaveCount(4);
  });

  test("applies species filter with live loading announcement", async ({ page }) => {
    const baselineCatch = buildCatchResponse({ nextCursor: "cursor-1", totalRows: 2000 });
    const filteredCatch = buildCatchResponse({
      species: "Yellowtail",
      nextCursor: null,
      totalRows: 1,
      data: [{ boat: "Yellowtail Express", topSpecies: "Yellowtail" }],
    });

    await page.route("**/offshore-catch**", async (route) => {
      const url = new URL(route.request().url());
      const species = url.searchParams.getAll("species");
      if (species.includes("Yellowtail")) {
        await delay(200);
        return fulfillJson(route, filteredCatch);
      }
      return fulfillJson(route, baselineCatch);
    });

    await page.route("**/offshore-metrics**", async (route) => {
      const url = new URL(route.request().url());
      const species = url.searchParams.getAll("species");
      if (species.includes("Yellowtail")) {
        await delay(200);
        return fulfillJson(route, FILTERED_METRICS);
      }
      return fulfillJson(route, BASE_METRICS);
    });

    await page.goto("/");

    const filterResponse = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("species=Yellowtail"),
    );

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: "Yellowtail" } }));
    });

    const loadingState = page.locator("#catchTableMount .state--loading");
    await expect(loadingState).toBeVisible();
    await expect(loadingState).toHaveAttribute("role", "status");
    await expect(loadingState).toHaveAttribute("aria-live", "polite");

    await filterResponse;

    const rows = page.locator("table.catch-table tbody tr");
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText("Yellowtail Express");
    await expect(page.locator(".summary-card__value").first()).toContainText("12");
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

    const emptyResponse = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("Ghost+Fish"),
    );

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: "Ghost Fish" } }));
    });

    await emptyResponse;

    await expect(page.locator(".state--empty")).toHaveText(/No results/i);
    await expect(page.locator("table.catch-table")).toHaveCount(0);
  });

  test("loads additional pages via load more tap", async ({ page }) => {
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
    await expect(loadMore).toBeVisible();

    const nextPageResponse = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("cursor=cursor-1"),
    );

    await loadMore.tap();
    await nextPageResponse;

    await expect(page.locator("table.catch-table tbody tr")).toHaveCount(3);
    await expect(loadMore).toHaveText(/All results loaded/i);
    await expect(loadMore).toBeDisabled();
    expect(catchCalls).toBeGreaterThanOrEqual(2);
  });

  test("announces errors via assertive live region", async ({ page }) => {
    const baselineCatch = buildCatchResponse({ nextCursor: null });

    await page.route("**/offshore-catch**", (route) => {
      const url = new URL(route.request().url());
      if (url.searchParams.getAll("species").includes("TriggerError")) {
        return route.fulfill({ status: 500, body: "server error" });
      }
      return fulfillJson(route, baselineCatch);
    });

    await page.route("**/offshore-metrics**", (route) => {
      const url = new URL(route.request().url());
      if (url.searchParams.getAll("species").includes("TriggerError")) {
        return route.fulfill({ status: 500, body: "server error" });
      }
      return fulfillJson(route, BASE_METRICS);
    });

    await page.goto("/");

    const errorResponse = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.status() === 500,
    );

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: "TriggerError" } }));
    });

    await errorResponse;

    const tableError = page.locator("#catchTableMount .state--error");
    await expect(tableError).toBeVisible();
    await expect(tableError).toHaveAttribute("role", "alert");
    await expect(tableError).toHaveAttribute("aria-live", "assertive");
    await expect(tableError).toContainText(/Unable to load fishing data/i);

    const metricsError = page.locator("#statsGridContainer .state--error");
    await expect(metricsError).toBeVisible();
    await expect(metricsError).toHaveAttribute("role", "alert");
    await expect(metricsError).toHaveAttribute("aria-live", "assertive");
    await expect(metricsError).toContainText(/Summary metrics unavailable/i);
  });
});
