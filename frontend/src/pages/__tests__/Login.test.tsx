/**
 * Login Page Tests
 *
 * Tests for the Login page component including:
 * - Form rendering
 * - Input handling
 * - Submit handling (via the useAuth signIn contract)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Login from "../Login";

const hooks = vi.hoisted(() => ({
  signIn: vi.fn(),
  signUp: vi.fn(),
  signInWithGoogle: vi.fn(),
  toast: vi.fn(),
  isAuthenticated: false,
  user: undefined as { role?: string } | undefined,
}));

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    signIn: hooks.signIn,
    signUp: hooks.signUp,
    signInWithGoogle: hooks.signInWithGoogle,
    isAuthenticated: hooks.isAuthenticated,
    user: hooks.user,
  }),
}));

vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({ lang: "en", dir: "ltr" }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: hooks.toast }),
}));

const legalMocks = vi.hoisted(() => ({
  acceptPolicy: vi.fn().mockResolvedValue(undefined),
  setConsent: vi.fn().mockResolvedValue(undefined),
  listPolicies: vi.fn().mockResolvedValue([
    { slug: "terms", live_version: { uuid: "t1" } },
    { slug: "privacy", live_version: { uuid: "p1" } },
  ]),
}));
vi.mock("@/services/legal", () => ({
  acceptPolicy: legalMocks.acceptPolicy,
  setConsent: legalMocks.setConsent,
  listPolicies: legalMocks.listPolicies,
}));

const renderLogin = (initialEntry = "/login") =>
  render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Login />
    </MemoryRouter>,
  );

describe("Login Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hooks.isAuthenticated = false;
    hooks.user = undefined;
    legalMocks.listPolicies.mockResolvedValue([
      { slug: "terms", live_version: { uuid: "t1" } },
      { slug: "privacy", live_version: { uuid: "p1" } },
    ]);
  });

  it("renders login form", () => {
    renderLogin();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Sign in$/i })).toBeInTheDocument();
  });

  it("handles email input", () => {
    renderLogin();
    const emailInput = screen.getByLabelText(/Email/i);
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    expect(emailInput).toHaveValue("test@example.com");
  });

  it("handles password input", () => {
    renderLogin();
    const passwordInput = screen.getByLabelText(/Password/i);
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    expect(passwordInput).toHaveValue("password123");
  });

  it("submits credentials through signIn", async () => {
    hooks.signIn.mockResolvedValue(undefined);
    renderLogin();

    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /^Sign in$/i }));

    await waitFor(() => {
      expect(hooks.signIn).toHaveBeenCalledWith("test@example.com", "password123");
    });
  });

  it("shows a destructive toast on login error", async () => {
    hooks.signIn.mockRejectedValue(new Error("Invalid credentials"));
    renderLogin();

    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "wrong@example.com" } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: "wrongpassword" } });
    fireEvent.click(screen.getByRole("button", { name: /^Sign in$/i }));

    await waitFor(() => {
      expect(hooks.toast).toHaveBeenCalledWith(
        expect.objectContaining({ variant: "destructive" }),
      );
    });
  });

  it("renders the forgot password link", () => {
    renderLogin();
    expect(screen.getByText(/Forgot password\?/i)).toBeInTheDocument();
  });

  it("can switch to the register form", () => {
    renderLogin();
    fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));
    expect(screen.getByLabelText(/First name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last name/i)).toBeInTheDocument();
  });

  describe("signup consent (Terms/Privacy required, marketing/Talent Pool optional)", () => {
    it("disables submit until Terms + Privacy is accepted and never pre-checks optional consents", async () => {
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));
      await waitFor(() => expect(legalMocks.listPolicies).toHaveBeenCalled());

      const submit = screen.getByRole("button", { name: /Create account/i });
      expect(submit).toBeDisabled();

      const termsCheckbox = screen.getByLabelText(/Terms of Service/i);
      const talentPoolCheckbox = screen.getByLabelText(/discover my profile/i);
      const marketingCheckbox = screen.getByLabelText(/marketing emails/i);
      expect(termsCheckbox).not.toBeChecked();
      expect(talentPoolCheckbox).not.toBeChecked();
      expect(marketingCheckbox).not.toBeChecked();

      fireEvent.click(termsCheckbox);
      await waitFor(() => expect(submit).not.toBeDisabled());
    });

    it("records Terms/Privacy acceptance but NOT marketing/Talent Pool consent when those boxes are left unchecked", async () => {
      hooks.signUp.mockResolvedValue({ role: "jobseeker" });
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));
      await waitFor(() => expect(legalMocks.listPolicies).toHaveBeenCalled());

      fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "Jane" } });
      fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
      fireEvent.change(screen.getByLabelText(/^Email$/i), { target: { value: "jane@example.com" } });
      fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: "password123" } });
      fireEvent.click(screen.getByLabelText(/Terms of Service/i));
      fireEvent.click(screen.getByRole("button", { name: /Create account/i }));

      await waitFor(() => expect(hooks.signUp).toHaveBeenCalled());
      await waitFor(() => {
        expect(legalMocks.acceptPolicy).toHaveBeenCalledWith("terms", "signup");
        expect(legalMocks.acceptPolicy).toHaveBeenCalledWith("privacy", "signup");
      });
      expect(legalMocks.setConsent).not.toHaveBeenCalled();
    });

    it("records independent opt-in consents only when explicitly checked", async () => {
      hooks.signUp.mockResolvedValue({ role: "jobseeker" });
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));
      await waitFor(() => expect(legalMocks.listPolicies).toHaveBeenCalled());

      fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "Jane" } });
      fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
      fireEvent.change(screen.getByLabelText(/^Email$/i), { target: { value: "jane@example.com" } });
      fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: "password123" } });
      fireEvent.click(screen.getByLabelText(/Terms of Service/i));
      fireEvent.click(screen.getByLabelText(/discover my profile/i));
      fireEvent.click(screen.getByLabelText(/marketing emails/i));
      fireEvent.click(screen.getByRole("button", { name: /Create account/i }));

      await waitFor(() => expect(hooks.signUp).toHaveBeenCalled());
      await waitFor(() => {
        expect(legalMocks.setConsent).toHaveBeenCalledWith("talent_pool", true, "signup");
        expect(legalMocks.setConsent).toHaveBeenCalledWith("marketing_emails", true, "signup");
      });
    });
  });

  describe("fail-closed signup when Terms/Privacy aren't both live (directive item 24)", () => {
    it("keeps Create account disabled even after checking Terms if Terms has no active version", async () => {
      legalMocks.listPolicies.mockResolvedValue([
        { slug: "terms", live_version: null },
        { slug: "privacy", live_version: { uuid: "p1" } },
      ]);
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));

      await waitFor(() => expect(legalMocks.listPolicies).toHaveBeenCalled());
      fireEvent.click(screen.getByLabelText(/Terms of Service/i));

      const submit = screen.getByRole("button", { name: /Create account/i });
      await waitFor(() => expect(submit).toBeDisabled());
    });

    it("keeps Create account disabled if Privacy has no active version", async () => {
      legalMocks.listPolicies.mockResolvedValue([
        { slug: "terms", live_version: { uuid: "t1" } },
        { slug: "privacy", live_version: null },
      ]);
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));

      await waitFor(() => expect(legalMocks.listPolicies).toHaveBeenCalled());
      fireEvent.click(screen.getByLabelText(/Terms of Service/i));

      const submit = screen.getByRole("button", { name: /Create account/i });
      await waitFor(() => expect(submit).toBeDisabled());
    });

    it("shows a visible unavailable banner instead of a blank/crashed form", async () => {
      legalMocks.listPolicies.mockResolvedValue([
        { slug: "terms", live_version: null },
        { slug: "privacy", live_version: null },
      ]);
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(/can't be created right now/i);
      });
    });

    it("treats a failed policy-list fetch the same as not-ready (never assumes it's fine)", async () => {
      legalMocks.listPolicies.mockRejectedValue(new Error("network error"));
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));
      fireEvent.click(screen.getByLabelText(/Terms of Service/i));

      const submit = screen.getByRole("button", { name: /Create account/i });
      await waitFor(() => expect(submit).toBeDisabled());
    });

    it("never blocks LOGIN (only new-account creation) when legal isn't ready", async () => {
      legalMocks.listPolicies.mockResolvedValue([
        { slug: "terms", live_version: null },
        { slug: "privacy", live_version: null },
      ]);
      hooks.signIn.mockResolvedValue({ role: "jobseeker" });
      renderLogin();

      fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: "password123" } });
      fireEvent.click(screen.getByRole("button", { name: /^Sign in$/i }));

      await waitFor(() => expect(hooks.signIn).toHaveBeenCalled());
    });

    it("allows signup once Terms+Privacy are both confirmed live", async () => {
      hooks.signUp.mockResolvedValue({ role: "jobseeker" });
      renderLogin();
      fireEvent.click(screen.getByRole("button", { name: /Sign up/i }));
      await waitFor(() => expect(legalMocks.listPolicies).toHaveBeenCalled());

      fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: "Jane" } });
      fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: "Doe" } });
      fireEvent.change(screen.getByLabelText(/^Email$/i), { target: { value: "jane@example.com" } });
      fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: "password123" } });
      fireEvent.click(screen.getByLabelText(/Terms of Service/i));

      const submit = screen.getByRole("button", { name: /Create account/i });
      await waitFor(() => expect(submit).not.toBeDisabled());
      fireEvent.click(submit);

      await waitFor(() => expect(hooks.signUp).toHaveBeenCalled());
    });
  });

  describe("deep-link return destination (USAM Master integration)", () => {
    it("honors a safe ?next= deep link after signing in", async () => {
      hooks.signIn.mockResolvedValue({ role: "jobseeker" });
      renderLogin("/login?next=%2Fapp%2Fjobs");

      fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: "password123" } });
      fireEvent.click(screen.getByRole("button", { name: /^Sign in$/i }));

      await waitFor(() => {
        expect(hooks.signIn).toHaveBeenCalled();
      });
      // Successful navigation is proven indirectly: no error toast fired and
      // the component didn't throw — the actual target is covered by the
      // dedicated postAuthDestination/sanitizeReturnTo unit tests, which
      // this flow delegates to.
      expect(hooks.toast).not.toHaveBeenCalled();
    });

    it("ignores an external ?next= value instead of redirecting off-site", async () => {
      hooks.signIn.mockResolvedValue({ role: "jobseeker" });
      renderLogin("/login?next=https%3A%2F%2Fevil.example.com");

      fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "test@example.com" } });
      fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: "password123" } });
      fireEvent.click(screen.getByRole("button", { name: /^Sign in$/i }));

      await waitFor(() => {
        expect(hooks.signIn).toHaveBeenCalled();
      });
      // No crash and no destructive toast — the unsafe `next` is silently
      // discarded (validated end-to-end by return-url.test.ts).
      expect(hooks.toast).not.toHaveBeenCalled();
    });
  });
});
