/**
 * RashidWidget Component Tests
 *
 * The widget renders a floating Rasheed character for authenticated users and
 * renders nothing for anonymous users. These tests assert that observable
 * contract rather than internal chat wiring.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RashidWidget } from "../rashid/RashidWidget";

const state = vi.hoisted(() => ({
  isAuthenticated: true,
}));

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    isAuthenticated: state.isAuthenticated,
    user: state.isAuthenticated ? { id: 1, email: "test@example.com" } : null,
  }),
}));

vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({ lang: "en", dir: "ltr" }),
}));

const renderWidget = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <RashidWidget />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("RashidWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    state.isAuthenticated = true;
  });

  it("renders the character trigger button when authenticated", () => {
    renderWidget();
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("renders nothing when not authenticated", () => {
    state.isAuthenticated = false;
    const { container } = renderWidget();
    expect(container).toBeEmptyDOMElement();
  });
});
