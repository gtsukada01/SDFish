import { devices, expect, test } from "@playwright/test";
import {
  API_BASE_URL,
  BASE_METRICS,
  EMPTY_METRICS,
  FILTERED_METRICS,
  buildCatchResponse,
  fulfillJson,
} from "./support/mock-fixtures";

const { deviceScaleFactor } = devices["Pixel 7"];

const pixel10 = {
  viewport: { width: 412, height: 915 },
  screen: { width: 412, height: 915 },
  userAgent:
    "Mozilla/5.0 (Linux; Android 15; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
  deviceScaleFactor,
  isMobile: true,
  hasTouch: true,
} as const;

test.describe.configure({ mode: "parallel" });

test.describe("pixel 10 responsive layout", () => {
  test.use(pixel10);

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

    const sidebar = page.locator(".sidebar");
    await expect(sidebar).toBeHidden();

    const columns = await page.locator(".app-layout").evaluate((node) =>
      window.getComputedStyle(node).gridTemplateColumns,
    );
    expect(columns.includes("240px")).toBe(false);

    const coarsePointer = await page.evaluate(() => window.matchMedia("(pointer: coarse)").matches);
    expect(coarsePointer).toBe(true);

    const rows = page.locator("table.catch-table tbody tr");
    await expect(rows).toHaveCount(2);
    await expect(rows.first()).toContainText("Pacific Pioneer");
    await expect(page.locator(".summary-grid .summary-card")).toHaveCount(4);
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

    const filterApplied = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("species=Yellowtail"),
    );

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: "Yellowtail" } }));
    });

    await filterApplied;

    const rows = page.locator("table.catch-table tbody tr");
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText("Yellowtail Express");

    const summaryValue = page.locator(".summary-card__value").first();
    await expect(summaryValue).toContainText("12");
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

    const emptyPromise = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("Ghost+Fish"),
    );

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: "Ghost Fish" } }));
    });

    await emptyPromise;

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

    const nextPagePromise = page.waitForResponse((response) =>
      response.url().includes("offshore-catch") && response.request().url().includes("cursor=cursor-1"),
    );

    await loadMore.tap();
    await nextPagePromise;

    await expect(page.locator("table.catch-table tbody tr")).toHaveCount(3);
    await expect(loadMore).toHaveText(/All results loaded/i);
    await expect(loadMore).toBeDisabled();
    expect(catchCalls).toBeGreaterThanOrEqual(2);
  });
});
