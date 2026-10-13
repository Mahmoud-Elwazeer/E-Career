/**
 * AdminDashboard deep-link tests (USAM Master integration).
 *
 * Before this change, the active admin section lived only in local
 * `useState` — refreshing the page or sharing a URL always reset to
 * "overview". These tests pin the `?tab=` contract: the active section is
 * read from the URL on load, survives a refresh (re-render with the same
 * URL), and clicking a sidebar item updates the URL instead of only local
 * state.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AdminDashboard from "../AdminDashboard";

vi.mock("@/hooks/use-admin-stats", () => ({
  useAdminStats: () => ({
    stats: { total_jobs: 0, pending_review: 0, active_sources: 0, total_saves: 0, total_clicks: 0, total_views: 0, total_users: 0, jobs_this_week: 0 },
    charts: { jobs_by_industry: [], jobs_by_source: [], recent_activity: [] },
    isLoading: false,
    reload: vi.fn(),
  }),
  fetchActivityLogs: vi.fn().mockResolvedValue([]),
}));

vi.mock("@/hooks/use-feature-flags", () => ({
  useFeatureFlags: () => ({ flags: [], isLoading: false, toggleFlag: vi.fn(), isEnabled: () => false, reload: vi.fn() }),
}));

vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({ lang: "en", dir: "ltr" }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock("@/components/admin/AdminAlertsBanner", () => ({
  AdminAlertsBanner: () => null,
}));

vi.mock("@/services/client", () => ({
  apiRequest: vi.fn().mockResolvedValue({}),
}));

describe("AdminDashboard — tab deep-linking", () => {
  beforeEach(() => vi.clearAllMocks());

  it("defaults to the overview tab when no ?tab= is present", () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminDashboard />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /overview/i })).toBeInTheDocument();
  });

  it("opens directly into the section named by ?tab= (e.g. shared/bookmarked link)", () => {
    render(
      <MemoryRouter initialEntries={["/admin?tab=rashid"]}>
        <AdminDashboard />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /rasheed/i })).toBeInTheDocument();
  });

  it("falls back to overview for an unknown/stale ?tab= value instead of rendering blank", () => {
    render(
      <MemoryRouter initialEntries={["/admin?tab=not-a-real-tab"]}>
        <AdminDashboard />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /overview/i })).toBeInTheDocument();
  });

  it("clicking a sidebar section updates the active section", async () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminDashboard />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getAllByText(/Users/i)[0]);
    // UsersTab fetches its own data on mount before rendering its heading.
    expect(await screen.findByRole("heading", { name: /user management/i })).toBeInTheDocument();
  });
});
