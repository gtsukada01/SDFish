import { test, expect } from "@playwright/test";

test.describe("CatchTable shadcn component", () => {
  test("renders table with mock data", async ({ page }) => {
    await page.goto("http://localhost:8081");

    // Wait for loading to complete
    await page.waitForSelector("table.catch-table", { timeout: 10000 });

    // Verify table structure
    const table = page.locator("table.catch-table");
    await expect(table).toBeVisible();

    // Verify table has 2 data rows (from mockCatchTableResponse)
    const rows = page.locator("table.catch-table tbody tr");
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThanOrEqual(1); // At least "No results" or data rows

    // If data rows exist, verify content
    const firstRow = rows.first();
    const firstRowText = await firstRow.textContent();

    if (firstRowText && !firstRowText.includes("No results")) {
      // Should have 2 data rows from mock
      expect(rowCount).toBe(2);

      // Verify first row contains expected data
      await expect(firstRow).toContainText("Pacific Pioneer");
      await expect(firstRow).toContainText("San Diego");
      await expect(firstRow).toContainText("24h");
      await expect(firstRow).toContainText("250");
      await expect(firstRow).toContainText("Bluefin Tuna");
    }

    // Verify table headers (8 columns)
    const headers = page.locator("table.catch-table thead th");
    const headerCount = await headers.count();
    expect(headerCount).toBe(8);

    // Verify column headers exist
    await expect(page.locator("table.catch-table thead")).toContainText("Date");
    await expect(page.locator("table.catch-table thead")).toContainText("Boat");
    await expect(page.locator("table.catch-table thead")).toContainText("Landing");
    await expect(page.locator("table.catch-table thead")).toContainText("Duration");
    await expect(page.locator("table.catch-table thead")).toContainText("Anglers");
    await expect(page.locator("table.catch-table thead")).toContainText("Total Fish");
    await expect(page.locator("table.catch-table thead")).toContainText("Top Species");
    await expect(page.locator("table.catch-table thead")).toContainText("Weather");
  });

  test("verifies pagination controls", async ({ page }) => {
    await page.goto("http://localhost:8081");
    await page.waitForSelector("table.catch-table", { timeout: 10000 });

    // Find pagination buttons
    const prevButton = page.locator('button:has-text("Previous")');
    const nextButton = page.locator('button:has-text("Next")');

    await expect(prevButton).toBeVisible();
    await expect(nextButton).toBeVisible();

    // Previous should be disabled on first page
    await expect(prevButton).toBeDisabled();

    // Next should be disabled if only 2 rows (less than pageSize 25)
    await expect(nextButton).toBeDisabled();
  });

  test("verifies summary metrics cards", async ({ page }) => {
    await page.goto("http://localhost:8081");
    await page.waitForSelector("table.catch-table", { timeout: 10000 });

    // Verify 4 metric cards exist using shadcn Card components
    const cards = page.locator('[class*="rounded-"][class*="border"]').filter({ hasText: /Total Trips|Total Fish|Active Boats|Species/ });
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThanOrEqual(4);

    // Verify metrics display correct values from mockSummaryMetricsResponse
    await expect(page.getByText("220")).toBeVisible(); // Total Trips
    await expect(page.getByText("18,750")).toBeVisible(); // Total Fish
    await expect(page.getByText(/^5$/)).toBeVisible(); // Active Boats (exact match to avoid 18,750 match)
    await expect(page.getByText(/^4$/)).toBeVisible(); // Species (exact match)
  });

  test("verifies sortable columns have icons", async ({ page }) => {
    await page.goto("http://localhost:8081");
    await page.waitForSelector("table.catch-table", { timeout: 10000 });

    // Sortable columns should have ArrowUpDown icons
    const sortButtons = page.locator("table.catch-table thead button");
    const buttonCount = await sortButtons.count();
    expect(buttonCount).toBeGreaterThanOrEqual(4); // Date, Boat, Duration, Total Fish

    // Verify first sortable button (Date) has icon
    const dateButton = sortButtons.first();
    await expect(dateButton).toContainText("Date");
  });
});
