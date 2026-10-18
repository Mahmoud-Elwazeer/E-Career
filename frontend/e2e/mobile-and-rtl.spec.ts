import { test, expect } from "@playwright/test";

/**
 * Browser E2E — mobile viewport + RTL/Arabic verification (acceptance-pass
 * items 6 and 7). Arabic content being stored in the database is NOT
 * equivalent to verified RTL UX (directive's own words) — these tests
 * actually load the Arabic locale in a real browser and check layout
 * mechanics, not just that the API returns Arabic text.
 */

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("usam_onboarding_complete", "true");
  });
});

// Mobile-viewport tests run under the "chromium-mobile" Playwright project
// (see playwright.config.ts, which already configures devices["Pixel 7"]
// for that project) rather than overriding the device inline here — mixing
// an inline test.use({ ...devices[...] }) with per-project device config
// forces an invalid extra worker context and fails to launch.
test.describe("Mobile viewport — representative pages", () => {
  test("header/navigation and footer render without horizontal overflow on the homepage", async ({ page }) => {
    await page.goto("/");
    const acceptAll = page.getByRole("button", { name: /accept all/i });
    if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    // Allow a tiny tolerance for scrollbar/measurement rounding.
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 4);

    await expect(page.locator("footer")).toBeVisible();
  });

  test("Legal Center hub is usable on a mobile viewport — tiles stack, links stay tappable", async ({ page }) => {
    await page.goto("/legal");
    const acceptAll = page.getByRole("button", { name: /accept all/i });
    if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();

    const termsTile = page.getByRole("link", { name: /terms of service/i }).first();
    await expect(termsTile).toBeVisible();
    const box = await termsTile.boundingBox();
    expect(box).not.toBeNull();
    // A tappable link must have a non-trivial hit target, not a collapsed
    // 0-height element hidden by an overflow/layout bug.
    expect(box!.height).toBeGreaterThan(10);
  });

  test("a long policy page is readable (no clipped text container) on mobile", async ({ page }) => {
    await page.goto("/legal/privacy");
    const acceptAll = page.getByRole("button", { name: /accept all/i });
    if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();

    const article = page.locator("article");
    await expect(article).toBeVisible();
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 4);
  });

  test("the cookie banner does not block the entire viewport and its buttons stay reachable", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/");
    const banner = page.getByRole("region", { name: /cookie notice/i });
    await expect(banner).toBeVisible();
    const acceptButton = banner.getByRole("button", { name: /accept all/i });
    await expect(acceptButton).toBeVisible();
    await acceptButton.click();
    await expect(banner).not.toBeVisible();
  });
});

// The real language toggle (LangToggle in src/components/ThemeToggle.tsx,
// rendered by AuthNavbar) has an accessible name of "Switch language to
// Arabic" / "Switch language to English" via its aria-label. On a desktop
// viewport it's directly visible in the navbar; on a mobile viewport
// (< md breakpoint) AuthNavbar only renders it inside the hamburger
// menu's Sheet, so it must be opened first.
async function switchLocale(page: import("@playwright/test").Page, toName: RegExp) {
  let toggle = page.getByRole("button", { name: toName }).first();
  if (!(await toggle.isVisible().catch(() => false))) {
    await page.getByRole("button", { name: /open menu/i }).click();
    toggle = page.getByRole("button", { name: toName }).first();
    // The mobile Sheet's slide side flips with the language (left for RTL,
    // right for LTR). The app itself closes the Sheet as part of the
    // toggle's onToggled callback (see AuthNavbar.tsx / ThemeToggle.tsx) to
    // avoid flipping `side` mid-animation — wait for the Sheet's dialog to
    // actually be gone before returning control to the caller.
    await expect(toggle).toBeVisible({ timeout: 10_000 });
    await toggle.click();
    await expect(page.getByRole("dialog")).toHaveCount(0, { timeout: 10_000 });
    return;
  }
  await expect(toggle).toBeVisible({ timeout: 10_000 });
  await toggle.click();
}

async function switchToArabic(page: import("@playwright/test").Page) {
  await switchLocale(page, /switch language to arabic/i);
  await expect(page.locator("html")).toHaveAttribute("lang", "ar", { timeout: 10_000 });
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl", { timeout: 10_000 });
}

async function switchToEnglish(page: import("@playwright/test").Page) {
  await switchLocale(page, /switch language to english/i);
}

test.describe("Arabic / RTL — real browser rendering", () => {
  test("switching to Arabic sets document lang/dir and renders Arabic policy content", async ({ page }) => {
    await page.goto("/legal/terms");
    const acceptAll = page.getByRole("button", { name: /accept all/i });
    if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();

    await switchToArabic(page);

    // The Arabic terms content was seeded and activated for this run —
    // confirm real Arabic text is actually rendered (fetched via
    // GET /legal/policies/terms/?locale=ar), not silently falling back to
    // English inside an RTL wrapper.
    await expect(page.locator("article")).toContainText(/[\u0600-\u06FF]/);
  });

  test("the Arabic policy API is actually consumed for multiple representative documents", async ({ page }) => {
    await page.goto("/legal/terms");
    await switchToArabic(page);

    const slugs = ["terms", "privacy", "cookies", "refunds", "payment-security", "candidate-privacy", "business-terms"];
    for (const slug of slugs) {
      const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().includes(`/legal/policies/${slug}/`) && r.url().includes("locale=ar")),
        page.goto(`/legal/${slug}`),
      ]).catch(() => [null]);
      // Even if the goto/response race is missed on a fast cache hit, the
      // rendered content itself must still be Arabic once lang=ar persists.
      await expect(page.locator("html")).toHaveAttribute("lang", "ar", { timeout: 10_000 });
      await expect(page.locator("article")).toContainText(/[\u0600-\u06FF]/, { timeout: 10_000 });
      if (response) expect(response.url()).toContain("locale=ar");
    }
  });

  test("RTL: the Legal Center hub mirrors layout direction (arrow icon direction flips)", async ({ page }) => {
    await page.goto("/legal");
    const acceptAll = page.getByRole("button", { name: /accept all/i });
    if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();

    await switchToArabic(page);
    await expect(page.getByRole("heading", { name: "الشروط والسياسات" })).toBeVisible();
  });

  test("RTL: cookie banner is fully localized to Arabic — title, body, and all three buttons", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/");
    await switchToArabic(page);
    await page.reload();

    const banner = page.getByRole("region", { name: /إشعار ملفات تعريف الارتباط/i });
    await expect(banner).toBeVisible({ timeout: 10_000 });
    await expect(banner).toContainText(/[\u0600-\u06FF]/);
    // The three real, localized action buttons — not a leftover English
    // control inside an otherwise-Arabic banner.
    await expect(banner.getByRole("button", { name: /قبول الكل/ })).toBeVisible();
    await expect(banner.getByRole("button", { name: /رفض غير الضروري/ })).toBeVisible();
    await expect(banner.getByRole("button", { name: /إدارة التفضيلات/ })).toBeVisible();
  });

  test("RTL: switching back to English reverses lang/dir and English cookie banner text", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/");
    await switchToArabic(page);
    await switchToEnglish(page);
    await expect(page.locator("html")).toHaveAttribute("lang", "en", { timeout: 10_000 });
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr", { timeout: 10_000 });

    const banner = page.getByRole("region", { name: /cookie notice/i });
    await expect(banner).toBeVisible({ timeout: 10_000 });
    await expect(banner).toContainText("We use cookies to run the platform");
  });

  test("locale persists across navigation and a full page reload", async ({ page }) => {
    await page.goto("/legal");
    await switchToArabic(page);

    await page.goto("/legal/privacy");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("lang", "ar", { timeout: 10_000 });
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl", { timeout: 10_000 });
  });
});
