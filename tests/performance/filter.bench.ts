process.on("uncaughtException", (error) => {
  console.error("[bench] uncaught exception", error);
  process.exit(1);
});

process.on("unhandledRejection", (reason) => {
  console.error("[bench] unhandled rejection", reason);
  process.exit(1);
});

import { chromium, devices } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

import {
  API_BASE_URL,
  BASE_METRICS,
  FILTERED_METRICS,
  buildCatchResponse,
  fulfillJson,
} from "../ui/support/mock-fixtures.js";

const DESKTOP = devices["Desktop Chrome"];

const MAX_MEDIAN_MS = Number(process.env.MAX_MEDIAN_MS ?? 2000);
const MAX_P95_MS = Number(process.env.MAX_P95_MS ?? 2500);

interface Scenario {
  species: string;
  label: string;
  expectedBoat: string;
  catchResponse: ReturnType<typeof buildCatchResponse>;
  metricsResponse: unknown;
}

const baselineCatch = buildCatchResponse({ nextCursor: null, totalRows: 3 });

function buildMetricsForScenario({
  species,
  boat,
  totalFish,
  trips,
}: {
  species: string;
  boat: string;
  totalFish: number;
  trips: number;
}) {
  const topSpeciesCount = Math.min(totalFish, Math.round(totalFish * 0.6));
  return {
    fleet: {
      total_trips: trips,
      total_fish: totalFish,
      unique_boats: 1,
      unique_species: 1,
    },
    per_boat: [
      {
        boat,
        trips,
        total_fish: totalFish,
        top_species: species,
        top_species_count: topSpeciesCount,
      },
    ],
    per_species: [
      {
        species,
        total_fish: totalFish,
        boats: 1,
      },
    ],
    filters_applied: {
      start_date: "2025-08-01",
      end_date: "2025-09-30",
      species: [species],
      landing: null,
      boat: null,
    },
    last_synced_at: "2025-09-30T12:00:00Z",
  } as const;
}

const scenarios: Scenario[] = [
  {
    species: "Yellowtail",
    label: "yellowtail",
    expectedBoat: "Yellowtail Express",
    catchResponse: buildCatchResponse({
      species: "Yellowtail",
      nextCursor: null,
      totalRows: 1,
      data: [{ boat: "Yellowtail Express", topSpecies: "Yellowtail" }],
    }),
    metricsResponse: FILTERED_METRICS,
  },
  {
    species: "Bluefin Tuna",
    label: "bluefin",
    expectedBoat: "Bluefin Voyager",
    catchResponse: buildCatchResponse({
      species: "Bluefin Tuna",
      nextCursor: null,
      totalRows: 1,
      data: [{ boat: "Bluefin Voyager", topSpecies: "Bluefin Tuna" }],
    }),
    metricsResponse: buildMetricsForScenario({
      species: "Bluefin Tuna",
      boat: "Bluefin Voyager",
      totalFish: 720,
      trips: 9,
    }),
  },
  {
    species: "Dorado",
    label: "dorado",
    expectedBoat: "Dorado Runner",
    catchResponse: buildCatchResponse({
      species: "Dorado",
      nextCursor: null,
      totalRows: 1,
      data: [{ boat: "Dorado Runner", topSpecies: "Dorado" }],
    }),
    metricsResponse: buildMetricsForScenario({
      species: "Dorado",
      boat: "Dorado Runner",
      totalFish: 540,
      trips: 7,
    }),
  },
];

const scenarioBySpecies = new Map(scenarios.map((scenario) => [scenario.species, scenario]));

const traceDir = path.join(process.cwd(), "test-results", "perf-traces");
const tracePath = path.join(traceDir, `filter-bench-${Date.now()}.zip`);

function matchesScenario(responseUrl: string, species: string): boolean {
  const searchParams = new URL(responseUrl).searchParams;
  const speciesParams = searchParams.getAll("species");
  return speciesParams.includes(species);
}

async function ensureTableHydrated(page: import("@playwright/test").Page, expectedBoat: string) {
  await page.waitForFunction((boat) => {
    const selector = document.querySelector(
      "table.catch-table tbody tr td:nth-child(2)",
    );
    return selector ? selector.textContent?.includes(boat) ?? false : false;
  }, expectedBoat);
}

async function runScenario(
  page: import("@playwright/test").Page,
  scenario: Scenario,
): Promise<number> {
  const catchResponse = page.waitForResponse(
    (response) =>
      response.url().includes("offshore-catch") &&
      matchesScenario(response.url(), scenario.species),
  );
  const metricsResponse = page.waitForResponse(
    (response) =>
      response.url().includes("offshore-metrics") &&
      matchesScenario(response.url(), scenario.species),
  );
  const networkIdle = page.waitForLoadState("networkidle");
  const hydration = ensureTableHydrated(page, scenario.expectedBoat);

  const start = Date.now();
  await page.evaluate((value) => {
    document.dispatchEvent(new CustomEvent("mock-filter", { detail: { species: value } }));
  }, scenario.species);

  await Promise.all([catchResponse, metricsResponse, networkIdle, hydration]);
  return Date.now() - start;
}

(async () => {
  await fs.mkdir(traceDir, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({ ...DESKTOP });
  await context.tracing.start({ snapshots: true, screenshots: false });

  const page = await context.newPage();

  let traceStopped = false;

  try {
    await page.addInitScript(({ baseUrl }) => {
      (window as any).FISH_USE_MOCKS = false;
      (window as any).FISH_API_BASE_URL = baseUrl;
    }, { baseUrl: API_BASE_URL });

    await page.route("**/offshore-catch**", async (route) => {
      const url = route.request().url();
      const searchParams = new URL(url).searchParams;
      const species = searchParams.getAll("species")[0] ?? null;
      const scenarioMatch = species ? scenarioBySpecies.get(species) : undefined;
      await fulfillJson(route, scenarioMatch?.catchResponse ?? baselineCatch);
    });

    await page.route("**/offshore-metrics**", async (route) => {
      const url = route.request().url();
      const searchParams = new URL(url).searchParams;
      const species = searchParams.getAll("species")[0] ?? null;
      const scenarioMatch = species ? scenarioBySpecies.get(species) : undefined;
      const payload = scenarioMatch?.metricsResponse ?? BASE_METRICS;
      await fulfillJson(route, payload);
    });

    await page.goto("http://localhost:4173");

    await ensureTableHydrated(page, "Pacific Pioneer");

    const timings: Array<{ label: string; duration: number }> = [];

    for (const scenario of scenarios) {
      const duration = await runScenario(page, scenario);
      timings.push({ label: scenario.label, duration });
      console.log(`⏱️  ${scenario.label} filter: ${duration}ms`);
    }

    const sorted = timings
      .map((entry) => entry.duration)
      .sort((a, b) => a - b);

    if (sorted.length === 0) {
      throw new Error("No timings collected during filter benchmark");
    }

    const median = sorted[Math.floor(sorted.length / 2)] ?? 0;
    const p95Index = Math.min(sorted.length - 1, Math.ceil(sorted.length * 0.95) - 1);
    const p95 = sorted[p95Index] ?? median;

    if (median > MAX_MEDIAN_MS) {
      throw new Error(`Median filter response ${median}ms exceeds ${MAX_MEDIAN_MS}ms`);
    }

    if (p95 > MAX_P95_MS) {
      throw new Error(`P95 filter response ${p95}ms exceeds ${MAX_P95_MS}ms`);
    }

    console.log(`Median: ${median}ms, P95: ${p95}ms`);

    await context.tracing.stop({ path: tracePath });
    traceStopped = true;
  } finally {
    if (!traceStopped) {
      try {
        await context.tracing.stop({ path: tracePath });
      } catch {
        // ignore tracing stop errors during teardown
      }
    }
    await browser.close();
  }
})();
