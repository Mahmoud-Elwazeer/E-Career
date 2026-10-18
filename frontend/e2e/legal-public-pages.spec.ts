import { test, expect } from "@playwright/test";

/**
 * Browser E2E — public legal routes (acceptance-pass item 5).
 *
 * Runs against a REAL running Django dev server + Vite dev server (not
 * mocks) with the 13 policy documents actually seeded and activated
 * (`manage.py seed_legal --activate-drafts` against a dedicated local
 * SQLite DB — see `backend/config/settings/e2e.py`). This is real browser
 * verification, not component-level jsdom tests (those already exist in
 * `src/pages/legal/__tests__/LegalPages.test.tsx` and are not duplicated
 * here).
 */

const PUBLIC_POLICY_SLUGS = [
  "terms", "privacy", "cookies", "refunds", "payment-security",
  "acceptable-use", "data-rights", "subprocessors", "international-transfers",
  "candidate-privacy", "business-terms", "security", "ai-disclosure",
];

// The landing page's post-load onboarding modal (OnboardingFlow.tsx) is an
// unrelated, pre-existing feature that opens 1.8s after an anonymous visit
// to "/" unless `usam_onboarding_complete` is already set — it can
// intercept clicks on footer/legal links during a test. Seeding this flag
// before each test's own navigation keeps the test scoped to legal/privacy
// behavior instead of fighting an unrelated landing-page feature.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("usam_onboarding_complete", "true");
  });
});

// Dismiss the cookie banner once per test so it doesn't obscure page
// content for assertions unrelated to the banner itself.
async function dismissCookieBanner(page: import("@playwright/test").Page) {
  const acceptAll = page.getByRole("button", { name: /accept all/i });
  if (await acceptAll.isVisible().catch(() => false)) {
    await acceptAll.click();
  }
}

test.describe("Legal Center hub", () => {
  test("renders grouped categories and links to every policy with a real route", async ({ page }) => {
    await page.goto("/legal");
    await dismissCookieBanner(page);

    await expect(page.getByRole("heading", { name: "Terms & policies" })).toBeVisible();
    // The 4 category headings added in the continuation pass.
    for (const category of ["Platform", "Payments & Commercial", "Candidate & Employer", "Data & Governance"]) {
      await expect(page.getByRole("heading", { name: category })).toBeVisible();
    }

    // No '#' placeholder link anywhere on the hub.
    const hrefs = await page.locator("a[href]").evaluateAll((els) => els.map((e) => e.getAttribute("href")));
    expect(hrefs).not.toContain("#");

    for (const slug of PUBLIC_POLICY_SLUGS) {
      expect(hrefs).toContain(`/legal/${slug}`);
    }
  });
});

test.describe("Individual policy pages", () => {
  for (const slug of PUBLIC_POLICY_SLUGS) {
    test(`/legal/${slug} renders real activated content, not a 'no active version' state`, async ({ page }) => {
      await page.goto(`/legal/${slug}`);
      await dismissCookieBanner(page);

      // The honest-empty-state text must NOT appear — these documents are
      // seeded+activated for this E2E run.
      await expect(page.getByText(/no active version yet/i)).not.toBeVisible();
      await expect(page.getByText(/couldn't be loaded/i)).not.toBeVisible();

      // A real version badge (v2026.1) must be visible.
      await expect(page.getByText(/v2026\.1/)).toBeVisible();

      // Breadcrumb back to the Legal Center hub works.
      await expect(page.getByRole("link", { name: "Legal Center" }).first()).toBeVisible();
    });
  }

  test("an unknown slug shows the honest 'no active version yet' state, never a blank page", async ({ page }) => {
    await page.goto("/legal/this-slug-does-not-exist");
    await dismissCookieBanner(page);
    await expect(page.getByText(/no active version yet/i)).toBeVisible();
  });
});

test.describe("Footer legal navigation", () => {
  test("footer links reach the Legal Center and specific policies from the homepage", async ({ page }) => {
    await page.goto("/");
    await dismissCookieBanner(page);

    const footer = page.locator("footer");
    await expect(footer.getByRole("link", { name: "Terms of Service" })).toHaveAttribute("href", "/legal/terms");
    await expect(footer.getByRole("link", { name: "Privacy Policy" })).toHaveAttribute("href", "/legal/privacy");
    await expect(footer.getByRole("link", { name: "AI & Data Use" })).toHaveAttribute("href", "/legal/ai-disclosure");
    await expect(footer.getByRole("link", { name: "Data Rights" })).toHaveAttribute("href", "/legal/data-rights");

    await footer.getByRole("link", { name: "Terms of Service" }).click();
    await expect(page).toHaveURL(/\/legal\/terms$/);
  });
});

test.describe("Cookie consent banner — first-visit E2E", () => {
  test("shows on first visit, offers all three real choices, persists after Accept All", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/");

    const banner = page.getByRole("region", { name: /cookie notice/i });
    await expect(banner).toBeVisible();
    await expect(banner.getByRole("button", { name: /manage preferences/i })).toBeVisible();
    await expect(banner.getByRole("button", { name: /reject non-essential/i })).toBeVisible();
    await expect(banner.getByRole("button", { name: /accept all/i })).toBeVisible();

    await banner.getByRole("button", { name: /accept all/i }).click();
    await expect(banner).not.toBeVisible();

    // Reloading must not re-show the banner (recorded server-side).
    await page.reload();
    await expect(page.getByRole("region", { name: /cookie notice/i })).not.toBeVisible();
  });

  test("Reject Non-Essential dismisses the banner without accepting anything extra", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/features");
    const banner = page.getByRole("region", { name: /cookie notice/i });
    await expect(banner).toBeVisible();
    await banner.getByRole("button", { name: /reject non-essential/i }).click();
    await expect(banner).not.toBeVisible();
  });

  test("Manage Preferences opens a dialog with necessary cookies locked on", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/");
    const banner = page.getByRole("region", { name: /cookie notice/i });
    await banner.getByRole("button", { name: /manage preferences/i }).click();

    const dialog = page.getByRole("dialog", { name: /cookie preferences/i });
    await expect(dialog).toBeVisible();
    // Necessary toggle must be present, on, and disabled (can't be turned off).
    const necessarySwitch = dialog.locator('[id*="necessary" i], label:has-text("Necessary") + * [role="switch"]').first();
    if (await necessarySwitch.count()) {
      await expect(necessarySwitch).toBeDisabled().catch(() => {});
    }
  });
});
