import { defineConfig } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const PLAYWRIGHT_HOME = path.join(process.cwd(), ".playwright-home");
fs.mkdirSync(PLAYWRIGHT_HOME, { recursive: true });

export default defineConfig({
  testDir: "../tests/ui",
  fullyParallel: true,
  use: {
    channel: "chrome",
    headless: true,
    viewport: { width: 1280, height: 720 },
    trace: "retain-on-failure",
    launchOptions: {
      args: ["--disable-crashpad"],
      env: {
        HOME: PLAYWRIGHT_HOME,
      },
    },
    baseURL: "http://127.0.0.1:4173",
  },
  webServer: {
    command: "node ../scripts/serve-static.mjs",
    url: "http://127.0.0.1:4173",
    timeout: 120_000,
    reuseExistingServer: true,
  },
});
