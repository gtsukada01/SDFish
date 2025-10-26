import { test, expect } from "@playwright/test";

test.describe("FilterPanel Diagnostic Verification", () => {
  test("comprehensive FilterPanel verification", async ({ page }) => {
    // Navigate and wait
    await page.goto("http://localhost:8081");
    await page.waitForLoadState("networkidle");

    console.log("\n========================================");
    console.log("FILTERPANEL COMPONENT VERIFICATION");
    console.log("========================================\n");

    // 1. COMPONENT PRESENCE VERIFICATION
    console.log("1️⃣  COMPONENT PRESENCE:");

    // Calendar Date Pickers
    const startDateInput = page.locator('button:has-text("August 31st, 2025")');
    const endDateInput = page.locator('button:has-text("September 30th, 2025")');

    const startDateVisible = await startDateInput.isVisible();
    const endDateVisible = await endDateInput.isVisible();

    console.log(`   ✓ Start Date Picker: ${startDateVisible ? '✅ FOUND' : '❌ MISSING'}`);
    console.log(`   ✓ End Date Picker: ${endDateVisible ? '✅ FOUND' : '❌ MISSING'}`);

    // Select Dropdowns (use role="combobox" to target the actual Select components)
    const landingSelect = page.locator('[role="combobox"]').filter({ hasText: 'All Landings' });
    const boatSelect = page.locator('[role="combobox"]').filter({ hasText: 'All Boats' });

    const landingVisible = await landingSelect.isVisible();
    const boatVisible = await boatSelect.isVisible();

    console.log(`   ✓ Landing Select: ${landingVisible ? '✅ FOUND' : '❌ MISSING'}`);
    console.log(`   ✓ Boat Select: ${boatVisible ? '✅ FOUND' : '❌ MISSING'}`);

    // Species Badges
    const speciesBadges = [
      'Bluefin Tuna',
      'Yellowfin Tuna',
      'Yellowtail',
      'Dorado',
      'Skipjack',
      'Bonito'
    ];

    console.log(`   ✓ Species Badges:`);
    for (const species of speciesBadges) {
      const badge = page.locator(`button:has-text("${species}")`);
      const visible = await badge.isVisible();
      console.log(`     - ${species}: ${visible ? '✅' : '❌'}`);
    }

    // Reset Button
    const resetButton = page.locator('button:has-text("Reset")');
    const resetVisible = await resetButton.isVisible();
    console.log(`   ✓ Reset Button: ${resetVisible ? '✅ FOUND' : '❌ MISSING'}`);

    // 2. SHADCN STYLING VALIDATION
    console.log("\n2️⃣  SHADCN STYLING VALIDATION:");

    // Check date picker button classes
    const startDateClasses = await startDateInput.getAttribute('class') || '';
    console.log(`   ✓ Date Picker Classes: ${startDateClasses.includes('inline-flex') ? '✅ shadcn' : '⚠️  custom'}`);
    console.log(`     - inline-flex: ${startDateClasses.includes('inline-flex') ? '✅' : '❌'}`);
    console.log(`     - items-center: ${startDateClasses.includes('items-center') ? '✅' : '❌'}`);
    console.log(`     - justify-start: ${startDateClasses.includes('justify-start') ? '✅' : '❌'}`);

    // Check Select component classes
    const landingClasses = await landingSelect.getAttribute('class') || '';
    console.log(`   ✓ Select Classes: ${landingClasses.includes('flex') ? '✅ shadcn' : '⚠️  custom'}`);
    console.log(`     - flex: ${landingClasses.includes('flex') ? '✅' : '❌'}`);
    console.log(`     - w-full: ${landingClasses.includes('w-full') ? '✅' : '❌'}`);

    // Check Badge classes
    const bluefinBadge = page.locator('button:has-text("Bluefin Tuna")');
    const badgeClasses = await bluefinBadge.getAttribute('class') || '';
    console.log(`   ✓ Badge Classes: ${badgeClasses.includes('inline-flex') ? '✅ shadcn' : '⚠️  custom'}`);
    console.log(`     - inline-flex: ${badgeClasses.includes('inline-flex') ? '✅' : '❌'}`);
    console.log(`     - rounded-md: ${badgeClasses.includes('rounded') ? '✅' : '❌'}`);

    // Check Reset button classes
    const resetClasses = await resetButton.getAttribute('class') || '';
    console.log(`   ✓ Reset Button Classes: ${resetClasses.includes('inline-flex') ? '✅ shadcn' : '⚠️  custom'}`);

    // Check for HSL color tokens in computed styles
    const landingStyles = await page.evaluate(() => {
      const el = document.querySelector('[role="combobox"]');
      if (!el) return null;
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
        color: styles.color,
        borderColor: styles.borderColor
      };
    });

    console.log(`   ✓ HSL Color Tokens:`);
    console.log(`     - Background: ${landingStyles?.backgroundColor || 'N/A'}`);
    console.log(`     - Text: ${landingStyles?.color || 'N/A'}`);
    console.log(`     - Border: ${landingStyles?.borderColor || 'N/A'}`);

    // 3. INTERACTIVITY TESTING
    console.log("\n3️⃣  INTERACTIVITY TESTING:");

    // Test date picker click
    console.log(`   ✓ Testing Date Picker Popover...`);
    await startDateInput.click();
    await page.waitForTimeout(500);

    const calendar = page.locator('[role="dialog"]').or(page.locator('.rdp')).or(page.locator('[class*="calendar"]'));
    const calendarVisible = await calendar.isVisible().catch(() => false);
    console.log(`     - Calendar Popover Opens: ${calendarVisible ? '✅ YES' : '⚠️  NO'}`);

    if (calendarVisible) {
      await page.screenshot({ path: 'screenshots/calendar-popover-open.png' });
      // Close calendar
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    }

    // Test species badge selection
    console.log(`   ✓ Testing Species Badge Selection...`);
    const yellowtailBadge = page.locator('button:has-text("Yellowtail")');
    const initialClass = await yellowtailBadge.getAttribute('class');

    await yellowtailBadge.click();
    await page.waitForTimeout(300);

    const afterClickClass = await yellowtailBadge.getAttribute('class');
    const classChanged = initialClass !== afterClickClass;
    console.log(`     - Badge Visual State Changes: ${classChanged ? '✅ YES' : '⚠️  NO'}`);

    await page.screenshot({ path: 'screenshots/badge-selected.png' });

    // Test Landing select dropdown
    console.log(`   ✓ Testing Landing Select Dropdown...`);
    await landingSelect.click();
    await page.waitForTimeout(500);

    const dropdown = page.locator('[role="listbox"]').or(page.locator('[role="menu"]'));
    const dropdownVisible = await dropdown.isVisible().catch(() => false);
    console.log(`     - Dropdown Opens: ${dropdownVisible ? '✅ YES' : '⚠️  NO'}`);

    if (dropdownVisible) {
      await page.screenshot({ path: 'screenshots/select-dropdown-open.png' });
      await page.keyboard.press('Escape');
    }

    // Test Reset button
    console.log(`   ✓ Testing Reset Button...`);
    await resetButton.click();
    await page.waitForTimeout(500);
    console.log(`     - Reset Button Clickable: ✅ YES`);

    // 4. CONSOLE ERROR CHECK
    console.log("\n4️⃣  CONSOLE ERROR CHECK:");

    const errors: string[] = [];
    const warnings: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
      if (msg.type() === 'warning') warnings.push(msg.text());
    });

    // Trigger some interactions to capture any errors
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    if (errors.length === 0) {
      console.log(`   ✅ No Console Errors Detected`);
    } else {
      console.log(`   ❌ Console Errors Found (${errors.length}):`);
      errors.forEach(err => console.log(`     - ${err}`));
    }

    if (warnings.length > 0) {
      console.log(`   ⚠️  Console Warnings (${warnings.length}):`);
      warnings.slice(0, 3).forEach(warn => console.log(`     - ${warn}`));
    }

    // 5. FINAL SCREENSHOT
    await page.screenshot({ path: 'screenshots/filterpanel-final.png', fullPage: true });

    console.log("\n========================================");
    console.log("✅ VERIFICATION COMPLETE");
    console.log("========================================\n");
    console.log("Screenshots saved to:");
    console.log("  - screenshots/filterpanel-final.png");
    console.log("  - screenshots/calendar-popover-open.png");
    console.log("  - screenshots/badge-selected.png");
    console.log("  - screenshots/select-dropdown-open.png\n");
  });
});
