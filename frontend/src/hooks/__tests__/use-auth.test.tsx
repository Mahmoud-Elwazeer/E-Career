/**
 * useAuth Hook Tests
 *
 * Tests for the useAuth hook including:
 * - Login/logout flow
 * - Authentication state
 * - User data handling
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../use-auth";

// Hoisted mock fns so both the mock factory and the assertions share the same refs.
const authMocks = vi.hoisted(() => ({
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  resetPassword: vi.fn(),
  getMe: vi.fn(),
}));

const clientMocks = vi.hoisted(() => ({
  getAccessToken: vi.fn(),
  getRefreshToken: vi.fn(),
  clearTokens: vi.fn(),
}));

vi.mock("@/services/auth", () => ({
  login: authMocks.login,
  logout: authMocks.logout,
  register: authMocks.register,
  resetPassword: authMocks.resetPassword,
  getMe: authMocks.getMe,
}));

vi.mock("@/services/client", () => ({
  getAccessToken: clientMocks.getAccessToken,
  getRefreshToken: clientMocks.getRefreshToken,
  clearTokens: clientMocks.clearTokens,
}));

describe("useAuth Hook", () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    clientMocks.getAccessToken.mockReturnValue(null);
    clientMocks.getRefreshToken.mockReturnValue(null);
  });

  it("returns initial state when not authenticated", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    // With no token, loading resolves synchronously to false.
    await waitFor(() => expect(result.current.isLoading).toBe(false));
  });

  it("returns authenticated state when user has token", async () => {
    clientMocks.getAccessToken.mockReturnValue("fake-token");
    authMocks.getMe.mockResolvedValue({
      id: 1,
      email: "test@example.com",
      first_name: "Test",
      last_name: "User",
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).not.toBeNull();
      expect(result.current.user?.email).toBe("test@example.com");
    });
  });

  it("handles login successfully", async () => {
    authMocks.login.mockResolvedValue({
      user: {
        id: 1,
        email: "test@example.com",
        first_name: "Test",
        last_name: "User",
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.signIn("test@example.com", "password123");
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe("test@example.com");
    expect(result.current.user?.name).toBe("Test User");
  });

  it("handles logout successfully", async () => {
    clientMocks.getAccessToken.mockReturnValue("fake-token");
    clientMocks.getRefreshToken.mockReturnValue("fake-refresh");
    authMocks.getMe.mockResolvedValue({
      id: 1,
      email: "test@example.com",
      first_name: "Test",
      last_name: "User",
    });
    authMocks.logout.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    await act(async () => {
      await result.current.signOut();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("handles registration successfully", async () => {
    authMocks.register.mockResolvedValue({
      user: {
        id: 1,
        email: "newuser@example.com",
        first_name: "New",
        last_name: "User",
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.signUp("newuser@example.com", "password123", "New", "User");
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe("newuser@example.com");
  });

  it("handles password reset", async () => {
    authMocks.resetPassword.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    let response: { error: Error | null } = { error: new Error("unset") };
    await act(async () => {
      response = await result.current.resetPassword("test@example.com");
    });

    expect(response.error).toBeNull();
  });

  it("handles password reset error", async () => {
    authMocks.resetPassword.mockRejectedValue(new Error("User not found"));

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    let response: { error: Error | null } = { error: null };
    await act(async () => {
      response = await result.current.resetPassword("nonexistent@example.com");
    });

    expect(response.error).not.toBeNull();
    expect(response.error?.message).toBe("User not found");
  });

  it("handles auth:logout event", async () => {
    clientMocks.getAccessToken.mockReturnValue("fake-token");
    authMocks.getMe.mockResolvedValue({
      id: 1,
      email: "test@example.com",
      first_name: "Test",
      last_name: "User",
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    await act(async () => {
      window.dispatchEvent(new Event("auth:logout"));
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("normalizes user name correctly", async () => {
    clientMocks.getAccessToken.mockReturnValue("fake-token");
    authMocks.getMe.mockResolvedValue({
      id: 1,
      email: "test@example.com",
      name: "Full Name",
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.user?.name).toBe("Full Name");
    });
  });

  it("falls back to a default name when user data is missing", async () => {
    clientMocks.getAccessToken.mockReturnValue("fake-token");
    authMocks.getMe.mockResolvedValue({
      id: 1,
      email: "test@example.com",
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.user?.name).toBe("User");
    });
  });
});
