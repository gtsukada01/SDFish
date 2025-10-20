import { test, expect } from '@playwright/test';

test('date filter dropdown accepts selection', async ({ page }) => {
  // Navigate to the application
  await page.goto('http://localhost:8080/index.html');

  // Wait for the page to load
  await page.waitForLoadState('networkidle');

  // Enable console logging
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));

  // Wait for the date filter select to be visible
  const dateSelect = page.locator('button:has-text("Last 30 Days"), button:has-text("Last 7 Days"), button:has-text("Select date range")').first();
  await dateSelect.waitFor({ state: 'visible', timeout: 10000 });

  console.log('Current select text:', await dateSelect.textContent());

  // Click to open the dropdown
  await dateSelect.click();

  // Wait for dropdown to open
  await page.waitForTimeout(500);

  // Click on "Last 7 Days" option
  await page.locator('[role="option"]:has-text("Last 7 Days")').click();

  // Wait a bit for state update
  await page.waitForTimeout(1000);

  // Check if the selection was applied
  const updatedText = await dateSelect.textContent();
  console.log('Updated select text:', updatedText);

  expect(updatedText).toContain('Last 7 Days');
});
