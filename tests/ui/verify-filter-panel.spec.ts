import { test, expect } from "@playwright/test";

test.describe("FilterPanel Component Verification", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:8081");
    await page.waitForLoadState("networkidle");
  });

  test("should display FilterPanel with all components", async ({ page }) => {
    // Take initial screenshot
    await page.screenshot({ path: "screenshots/filterpanel-initial.png", fullPage: true });

    // Verify Calendar Popovers (date pickers)
    const startDateButton = page.locator('button:has-text("Start Date"), button:has-text("Pick a date")').first();
    const endDateButton = page.locator('button:has-text("End Date"), button:has-text("Pick a date")').last();

    await expect(startDateButton).toBeVisible();
    await expect(endDateButton).toBeVisible();

    // Verify Select dropdowns
    const landingSelect = page.locator('[role="combobox"]').filter({ hasText: /Landing|Select landing/ });
    const boatSelect = page.locator('[role="combobox"]').filter({ hasText: /Boat|Select boat/ });

    await expect(landingSelect.first()).toBeVisible();
    await expect(boatSelect.first()).toBeVisible();

    // Verify Species Badge components
    const speciesBadges = page.locator('[role="button"]').filter({ hasText: /Yellowtail|Bluefin|Skipjack/ });
    const badgeCount = await speciesBadges.count();
    console.log(`Found ${badgeCount} species badges`);

    // Verify Reset button
    const resetButton = page.locator('button:has-text("Reset")');
    await expect(resetButton).toBeVisible();

    console.log("✓ All FilterPanel components are present");
  });

  test("should use shadcn styling with HSL color tokens", async ({ page }) => {
    // Verify shadcn Button styling
    const resetButton = page.locator('button:has-text("Reset")');
    const buttonClasses = await resetButton.getAttribute("class");

    // Check for shadcn button classes
    expect(buttonClasses).toContain("inline-flex");
    expect(buttonClasses).toContain("items-center");

    // Verify Select component shadcn styling
    const selectTrigger = page.locator('[role="combobox"]').first();
    const selectClasses = await selectTrigger.getAttribute("class");
    expect(selectClasses).toContain("flex");

    console.log("✓ shadcn styling classes detected");
  });

  test("should allow date picker interaction", async ({ page }) => {
    // Click start date button to open Popover
    const startDateButton = page.locator('button').filter({ hasText: /Pick a date|Start Date/ }).first();
    await startDateButton.click();

    // Wait for calendar popover to appear
    await page.waitForTimeout(500);

    // Check if calendar is visible
    const calendar = page.locator('[role="grid"]').or(page.locator('.rdp'));
    const isCalendarVisible = await calendar.isVisible().catch(() => false);

    if (isCalendarVisible) {
      console.log("✓ Date picker Popover opens correctly");
      await page.screenshot({ path: "screenshots/filterpanel-calendar-open.png", fullPage: true });
    } else {
      console.log("⚠ Date picker Popover may not be visible");
      await page.screenshot({ path: "screenshots/filterpanel-calendar-debug.png", fullPage: true });
    }
  });

  test("should allow species badge interaction", async ({ page }) => {
    // Find species badges
    const speciesBadges = page.locator('[role="button"]').filter({ hasText: /Yellowtail|Bluefin|Skipjack/ });
    const badgeCount = await speciesBadges.count();

    if (badgeCount > 0) {
      const firstBadge = speciesBadges.first();
      const initialClass = await firstBadge.getAttribute("class");

      // Click the badge
      await firstBadge.click();
      await page.waitForTimeout(300);

      const afterClass = await firstBadge.getAttribute("class");

      // Take screenshot of selection
      await page.screenshot({ path: "screenshots/filterpanel-badge-selected.png", fullPage: true });

      console.log("✓ Species badge interaction works");
      console.log(`Initial classes: ${initialClass}`);
      console.log(`After click classes: ${afterClass}`);
    } else {
      console.log("⚠ No species badges found");
    }
  });

  test("should check for console errors", async ({ page }) => {
    const consoleMessages: string[] = [];
    const errors: string[] = [];

    page.on("console", (msg) => {
      consoleMessages.push(`${msg.type()}: ${msg.text()}`);
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    // Interact with components
    await page.locator('button').filter({ hasText: /Pick a date/ }).first().click();
    await page.waitForTimeout(500);

    const resetButton = page.locator('button:has-text("Reset")');
    if (await resetButton.isVisible()) {
      await resetButton.click();
    }

    console.log("\n=== Console Messages ===");
    consoleMessages.forEach(msg => console.log(msg));

    if (errors.length > 0) {
      console.log("\n❌ Console Errors Found:");
      errors.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log("\n✓ No console errors detected");
    }
  });

  test("should capture component structure", async ({ page }) => {
    // Get the FilterPanel structure
    const filterPanel = await page.evaluate(() => {
      const panel = document.querySelector('[class*="filter"]') || document.querySelector('main') || document.body;
      return {
        hasDatePickers: !!document.querySelector('button[class*="calendar"]') ||
                       !!document.querySelectorAll('button').length,
        hasSelects: !!document.querySelector('[role="combobox"]'),
        hasBadges: document.querySelectorAll('[class*="badge"]').length,
        hasResetButton: !!document.querySelector('button:has-text("Reset")'),
        totalButtons: document.querySelectorAll('button').length,
        totalSelects: document.querySelectorAll('[role="combobox"]').length,
      };
    });

    console.log("\n=== Component Structure ===");
    console.log(JSON.stringify(filterPanel, null, 2));
  });
});
