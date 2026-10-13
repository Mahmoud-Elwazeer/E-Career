/**
 * Legal Center + policy page tests.
 *
 *  - LegalCenter lists real routes to every public legal document (no `#`
 *    placeholders) and surfaces the unconfigured-entity notice honestly.
 *  - PolicyPage renders the active version's content and shows an honest
 *    "no active version yet" state instead of fabricating text when the
 *    backend has nothing published for a slug.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import LegalCenter from "../LegalCenter";
import PolicyPage from "../PolicyPage";

vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({ lang: "en", dir: "ltr" }),
}));
vi.mock("@/hooks/use-seo", () => ({
  usePageMeta: () => {},
}));
vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ isAuthenticated: false }),
}));
// These pages wrap content in the full site <Layout> (navbar/footer chrome).
// That chrome pulls in theme toggles, language switchers, etc. unrelated to
// what this test verifies — stub it to just render children.
vi.mock("@/components/Layout", () => ({
  Layout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const legalMocks = vi.hoisted(() => ({
  getLegalEntityPublic: vi.fn(),
  getPolicy: vi.fn(),
}));
vi.mock("@/services/legal", () => ({
  getLegalEntityPublic: legalMocks.getLegalEntityPublic,
  getPolicy: legalMocks.getPolicy,
}));

vi.mock("@/services/client", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

describe("LegalCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    legalMocks.getLegalEntityPublic.mockResolvedValue({
      legal_entity_name: "", registered_address: "", tax_or_registration_id: "",
      dpo_name: "", dpo_email: "", privacy_contact_email: "", support_contact_email: "",
      default_refund_window_days: null, is_configured: false, updated_at: "",
    });
  });

  it("links to every public legal document with real, working routes (no # placeholders)", async () => {
    render(<MemoryRouter><TooltipProvider><LegalCenter /></TooltipProvider></MemoryRouter>);
    const expected = ["/legal/terms", "/legal/privacy", "/legal/cookies", "/legal/refunds", "/legal/payment-security"];
    const links = await screen.findAllByRole("link");
    expect(links.some((l) => l.getAttribute("href") === "#")).toBe(false);
    const hrefs = links.map((l) => l.getAttribute("href"));
    for (const href of expected) {
      expect(hrefs).toContain(href);
    }
  });

  it("shows the unconfigured legal-entity notice when the backend hasn't configured one", async () => {
    render(<MemoryRouter><TooltipProvider><LegalCenter /></TooltipProvider></MemoryRouter>);
    expect(await screen.findByText(/REQUIRES LEGAL REVIEW \/ CONFIGURATION/i)).toBeInTheDocument();
  });
});

describe("PolicyPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the active policy version's content and version badge", async () => {
    legalMocks.getPolicy.mockResolvedValue({
      uuid: "v1", document_slug: "terms", document_title: "Terms of Service",
      version_label: "2026.1", locale: "en", jurisdiction: "OTHER", status: "active",
      content_markdown: "# Terms\nSome real terms text.",
      summary_of_changes: "", material_change: false, is_machine_translated: false,
      effective_at: "2026-01-01T00:00:00Z",
    });
    render(
      <MemoryRouter initialEntries={["/legal/terms"]}>
        <TooltipProvider>
          <Routes><Route path="/legal/:slug" element={<PolicyPage />} /></Routes>
        </TooltipProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByText(/Some real terms text/i)).toBeInTheDocument();
    expect(screen.getByText(/v2026\.1/)).toBeInTheDocument();
  });

  it("shows an honest 'no active version yet' message instead of fabricating content on 404", async () => {
    const { ApiError } = await import("@/services/client");
    legalMocks.getPolicy.mockRejectedValue(new (ApiError as any)("Not found", 404));
    render(
      <MemoryRouter initialEntries={["/legal/refunds"]}>
        <TooltipProvider>
          <Routes><Route path="/legal/:slug" element={<PolicyPage />} /></Routes>
        </TooltipProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByText(/No active version yet/i)).toBeInTheDocument();
  });
});
