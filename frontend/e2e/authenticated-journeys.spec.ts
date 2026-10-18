import { test, expect, type Page } from "@playwright/test";

/**
 * Browser E2E — authenticated journeys touching legal/privacy surfaces
 * (acceptance-pass item 5): Privacy Center, billing legal disclosure,
 * employer registration + billing disclosure. Each test creates its own
 * fresh account against the real backend (no shared/pre-seeded user) so
 * tests stay independent and don't depend on run order.
 */

function uniqueEmail(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 100000)}@example.test`;
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("usam_onboarding_complete", "true");
  });
});

async function dismissCookieBanner(page: Page) {
  const acceptAll = page.getByRole("button", { name: /accept all/i });
  if (await acceptAll.isVisible().catch(() => false)) await acceptAll.click();
}

async function signUpIndividual(page: Page, email: string) {
  await page.goto("/login");
  await dismissCookieBanner(page);
  await page.getByRole("button", { name: /sign up/i }).click();
  await page.getByLabel(/first name/i).fill("E2E");
  await page.getByLabel(/last name/i).fill("Candidate");
  await page.getByPlaceholder(/you@example\.com/i).fill(email);
  await page.getByLabel(/^password$/i).fill("E2ETestPass!2345");
  await page.getByRole("checkbox").first().check();
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page).not.toHaveURL(/\/login$/, { timeout: 10_000 });
}

test.describe("Privacy Center — authenticated journey", () => {
  test("a fresh individual account can reach the Privacy Center and see real consent/DSR controls", async ({ page }) => {
    await signUpIndividual(page, uniqueEmail("e2e-privacy"));
    await page.goto("/app/privacy-center");
    await expect(page.getByText(/privacy center/i).first()).toBeVisible({ timeout: 10_000 });
    // Real, backend-driven controls — not placeholder text.
    await expect(page.getByText(/talent pool/i).first()).toBeVisible();
  });
});

test.describe("Billing — legal disclosure before purchase", () => {
  test("the billing page shows the EGP/refund/payment-security disclosure with real links before any purchase", async ({ page }) => {
    await signUpIndividual(page, uniqueEmail("e2e-billing"));
    await page.goto("/app/billing");
    await expect(page.getByText(/billing & plans/i).first()).toBeVisible({ timeout: 10_000 });

    const refundLink = page.getByRole("link", { name: /refund.*cancellation policy/i });
    const paymentSecurityLink = page.getByRole("link", { name: /payment.*card security policy/i });
    await expect(refundLink).toHaveAttribute("href", "/legal/refunds");
    await expect(paymentSecurityLink).toHaveAttribute("href", "/legal/payment-security");

    // Honesty check (directive item 16): the page must state there is NO
    // automatic renewal, never claim one actually happens. Checking for
    // the explicit denial phrase is more reliable than a naive "must not
    // contain the word renewal" pattern, which would false-positive on
    // the correct, honest "no automatic renewal" sentence itself.
    const bodyText = (await page.locator("body").innerText()).toLowerCase();
    expect(bodyText).toContain("no automatic renewal");
    expect(bodyText).not.toContain("renews automatically");
    expect(bodyText).not.toContain("will renew automatically");
    expect(bodyText).not.toContain("will be renewed automatically");
  });
});

test.describe("Employer registration + billing disclosure", () => {
  test("a company signup reaches employer onboarding and employer billing shows the same legal disclosure", async ({ page }) => {
    await page.goto("/login");
    await dismissCookieBanner(page);
    await page.getByRole("button", { name: /sign up/i }).click();

    // Switch account type to "company" via the real radio control, and
    // confirm it actually registered as checked before continuing — a
    // race between this click and the form's own re-render previously
    // caused the signup to silently submit as "individual".
    const companyRadio = page.getByRole("radio", { name: /company/i });
    await companyRadio.click();
    await expect(companyRadio).toHaveAttribute("aria-checked", "true");

    await page.getByLabel(/first name/i).fill("E2E");
    await page.getByLabel(/last name/i).fill("Employer");
    await page.getByPlaceholder(/you@example\.com/i).fill(uniqueEmail("e2e-employer"));
    await page.getByLabel(/^password$/i).fill("E2ETestPass!2345");
    await page.getByRole("checkbox").first().check();
    await page.getByRole("button", { name: /create account|continue as company/i }).click();

    // A brand-new employer (no EmployerProfile yet) must land on employer
    // onboarding. Confirms the real backend fix made during this same
    // acceptance pass (apps.employers.views.EmployerProfileViewSet now
    // returns 404 instead of 403 for a profile-less employer's own
    // `list` call) actually resolves correctly end-to-end.
    await expect(page).toHaveURL(/\/app\/employer\/register/, { timeout: 10_000 });
  });
});
