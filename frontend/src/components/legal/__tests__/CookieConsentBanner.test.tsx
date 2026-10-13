/**
 * Cookie consent banner tests.
 *
 * Directive-mandated behaviors under test:
 *  - Offers Accept All / Reject Non-Essential / Manage Preferences (not just
 *    a single "Accept" button).
 *  - Works for an anonymous visitor (no auth) — the banner itself never
 *    requires login.
 *  - Necessary cookies are always forced true regardless of what's recorded.
 *  - Choices are persisted via the backend API, not just local storage.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CookieConsentBanner } from "../CookieConsentBanner";

const legalMocks = vi.hoisted(() => ({
  listCookieCategories: vi.fn(),
  getMyCookieConsent: vi.fn(),
  recordCookieConsent: vi.fn(),
}));

vi.mock("@/services/legal", () => ({
  listCookieCategories: legalMocks.listCookieCategories,
  getMyCookieConsent: legalMocks.getMyCookieConsent,
  recordCookieConsent: legalMocks.recordCookieConsent,
}));

vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({ lang: "en" }),
}));

const CATEGORIES = [
  { uuid: "1", key: "necessary", label: "Strictly necessary", description: "", is_essential: true, is_active: true },
  { uuid: "2", key: "functional", label: "Functional", description: "", is_essential: false, is_active: true },
  { uuid: "3", key: "analytics", label: "Analytics", description: "", is_essential: false, is_active: true },
  { uuid: "4", key: "marketing", label: "Marketing", description: "", is_essential: false, is_active: true },
];

describe("CookieConsentBanner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    legalMocks.listCookieCategories.mockResolvedValue(CATEGORIES);
    legalMocks.getMyCookieConsent.mockResolvedValue(null); // no prior consent -> show banner
    legalMocks.recordCookieConsent.mockResolvedValue({ uuid: "x", action: "accept_all", categories: {}, created_at: "" });
  });

  it("shows Accept All, Reject Non-Essential, and Manage Preferences — not a single Accept button", async () => {
    render(<CookieConsentBanner />);
    expect(await screen.findByRole("button", { name: /Accept all/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Reject non-essential/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Manage preferences/i })).toBeInTheDocument();
  });

  it("renders and functions without any authenticated user (anonymous visitor)", async () => {
    render(<CookieConsentBanner />);
    await waitFor(() => expect(legalMocks.getMyCookieConsent).toHaveBeenCalled());
    // No auth mock was ever provided to this component — it works regardless.
    expect(await screen.findByRole("button", { name: /Accept all/i })).toBeInTheDocument();
  });

  it("accepting all records necessary=true alongside the rest", async () => {
    render(<CookieConsentBanner />);
    const acceptAll = await screen.findByRole("button", { name: /Accept all/i });
    fireEvent.click(acceptAll);

    await waitFor(() => expect(legalMocks.recordCookieConsent).toHaveBeenCalled());
    const [action, categories] = legalMocks.recordCookieConsent.mock.calls[0];
    expect(action).toBe("accept_all");
    expect(categories.necessary).toBe(true);
  });

  it("rejecting non-essential still forces necessary=true", async () => {
    render(<CookieConsentBanner />);
    const reject = await screen.findByRole("button", { name: /Reject non-essential/i });
    fireEvent.click(reject);

    await waitFor(() => expect(legalMocks.recordCookieConsent).toHaveBeenCalled());
    const [action, categories] = legalMocks.recordCookieConsent.mock.calls[0];
    expect(action).toBe("reject_non_essential");
    expect(categories.necessary).toBe(true);
    expect(categories.marketing).toBe(false);
  });

  it("does not show the banner again if a consent record already exists", async () => {
    legalMocks.getMyCookieConsent.mockResolvedValue({
      uuid: "existing", action: "accept_all",
      categories: { necessary: true, functional: true, analytics: true, marketing: true },
      created_at: "2026-01-01",
    });
    render(<CookieConsentBanner />);
    await waitFor(() => expect(legalMocks.getMyCookieConsent).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByRole("region", { name: /Cookie notice/i })).not.toBeInTheDocument());
  });

  it("the necessary category toggle is always on and disabled in the manage dialog", async () => {
    render(<CookieConsentBanner />);
    const manageBtn = await screen.findByRole("button", { name: /Manage preferences/i });
    fireEvent.click(manageBtn);

    await waitFor(() => expect(screen.getByText(/Cookie preferences/i)).toBeInTheDocument());
    const necessarySwitch = screen.getByLabelText(/Strictly necessary/i);
    expect(necessarySwitch).toBeDisabled();
    expect(necessarySwitch).toHaveAttribute("data-state", "checked");
  });
});
