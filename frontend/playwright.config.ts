import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E config — acceptance pass, item 5 ("browser-based E2E is
 * now required"). This is the lightest viable addition: no E2E framework
 * existed before this pass (confirmed: no playwright/cypress dependency,
 * no e2e/ directory). Scoped to real-browser verification of the legal/
 * privacy/consent surface specifically, not a general E2E suite for the
 * whole app.
 *
 * Browser binary note: this sandbox has no outbound access to Playwright's
 * CDN to download its bundled Chromium, so these tests drive the system-
 * installed Google Chrome via `channel: "chrome"` instead of Playwright's
 * own browser binary. A CI/dev machine with internet access can instead
 * run `npx playwright install chromium` and drop the `channel` option for
 * Playwright's normally-pinned browser build — both are valid; this repo
 * defaults to the system-browser path since that's what actually works in
 * this environment, and is documented here so it's not mistaken for an
 * oversight.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"], ["json", { outputFile: "e2e-results.json" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium-desktop",
      use: { ...devices["Desktop Chrome"], channel: "chrome" },
      // mobile-and-rtl.spec.ts has its own dedicated mobile-viewport
      // tests run only under chromium-mobile below (and its RTL tests are
      // desktop-sized, so this project runs the RTL half of that file).
      testIgnore: /mobile-and-rtl\.spec\.ts/,
    },
    {
      name: "chromium-mobile",
      use: { ...devices["Pixel 7"], channel: "chrome" },
      testMatch: /mobile-and-rtl\.spec\.ts/,
    },
  ],
});
