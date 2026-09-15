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
}));

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    signIn: hooks.signIn,
    signUp: hooks.signUp,
    signInWithGoogle: hooks.signInWithGoogle,
    isAuthenticated: false,
  }),
}));

vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({ lang: "en", dir: "ltr" }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: hooks.toast }),
}));

const renderLogin = () =>
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <Login />
    </MemoryRouter>,
  );

describe("Login Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
});
