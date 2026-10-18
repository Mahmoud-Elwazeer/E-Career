import { test, expect } from "@playwright/test";

/**
 * Browser E2E — signup fail-closed gate + consent acknowledgement
 * (acceptance-pass item 5). Runs against the real Login.tsx page, real
 * backend-seeded+activated Terms/Privacy, and a real account-creation
 * request.
 */

function uniqueEmail() {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 100000)}@example.test`;
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("usam_onboarding_complete", "true");
  });
});

test.describe("Signup — legal gate resolves to the active Terms/Privacy version", () => {
  test("register tab shows the required Terms checkbox and submits successfully when Terms/Privacy are active", async ({ page }) => {
    await page.goto("/login");
    // Dismiss cookie banner if present.
    const acceptAll = page.getByRole("button", { name: /accept all/i });
    if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();

    await page.getByRole("button", { name: /sign up/i }).click();
    await expect(page.getByRole("heading", { name: /create account/i })).toBeVisible();

    // Required Terms acknowledgement checkbox references real policy links.
    const termsLink = page.getByRole("link", { name: /terms/i }).first();
    await expect(termsLink).toHaveAttribute("href", /\/legal\/terms/);

    await page.getByLabel(/first name/i).fill("E2E");
    await page.getByLabel(/last name/i).fill("Tester");
    await page.getByPlaceholder(/you@example\.com/i).fill(uniqueEmail());
    await page.getByLabel(/^password$/i).fill("E2ETestPass!2345");

    // Submit must be disabled until the Terms checkbox is checked.
    const submit = page.getByRole("button", { name: /create account/i });
    await expect(submit).toBeDisabled();

    const termsCheckbox = page.getByRole("checkbox").first();
    await termsCheckbox.check();
    await expect(submit).toBeEnabled();

    await submit.click();
    // A successful signup navigates away from /login (to a dashboard or
    // employer onboarding) — confirms the whole gate -> accept -> create
    // pipeline actually completed against the real backend.
    await expect(page).not.toHaveURL(/\/login$/, { timeout: 10_000 });
  });

  test("optional marketing and Talent Pool consent checkboxes are never pre-checked", async ({ page }) => {
    await page.goto("/login");
    const acceptAll = page.getByRole("button", { name: /accept all/i });
    if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();
    await page.getByRole("button", { name: /sign up/i }).click();

    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    for (let i = 0; i < count; i++) {
      await expect(checkboxes.nth(i)).not.toBeChecked();
    }
  });
});
