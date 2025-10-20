import { test } from "@playwright/test";

test("inspect species badges DOM", async ({ page }) => {
  await page.goto("http://localhost:8081");
  await page.waitForLoadState("networkidle");

  // Find the actual structure
  const badgeInfo = await page.evaluate(() => {
    const speciesLabel = Array.from(document.querySelectorAll('*')).find(
      el => el.textContent?.trim() === 'Species'
    );

    if (!speciesLabel) return { error: 'Species label not found' };

    // Look at parent and next sibling
    const parent = speciesLabel.parentElement;
    const grandParent = parent?.parentElement;
    const nextSibling = parent?.nextElementSibling;

    const parentButtons = parent?.querySelectorAll('button') || [];
    const nextSiblingButtons = nextSibling?.querySelectorAll('button') || [];
    const grandParentButtons = grandParent?.querySelectorAll('button') || [];

    // Find all buttons containing species names
    const allButtons = Array.from(document.querySelectorAll('button'));
    const allButtonTexts = allButtons.map(btn => btn.textContent?.trim());

    // Look for buttons near "Species" label
    const nearbyButtons = grandParent?.querySelectorAll('button') || [];

    return {
      parentClass: parent?.className,
      nextSiblingClass: nextSibling?.className,
      totalButtonsOnPage: allButtons.length,
      allButtonTexts: allButtonTexts.slice(0, 20), // First 20 buttons
      grandParentButtonCount: nearbyButtons.length,
      nearbyButtonTexts: Array.from(nearbyButtons).map(btn => btn.textContent?.trim()),
      speciesLabelHTML: speciesLabel.parentElement?.innerHTML.substring(0, 500)
    };
  });

  console.log("\n=== SPECIES BADGE DOM STRUCTURE ===");
  console.log(JSON.stringify(badgeInfo, null, 2));

  // Take screenshot
  await page.screenshot({ path: 'screenshots/badge-inspect.png', fullPage: true });
});
