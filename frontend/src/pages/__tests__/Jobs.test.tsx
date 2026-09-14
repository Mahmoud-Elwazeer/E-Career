/**
 * Jobs Page Tests
 *
 * - Job list rendering
 * - Loading state handling
 * - Empty state handling
 * - Error state handling (retryable)
 * - Pagination
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Jobs from "../Jobs";

const mocks = vi.hoisted(() => ({
  fetchJobs: vi.fn(),
}));

vi.mock("@/services/jobs", () => ({
  fetchJobs: mocks.fetchJobs,
}));

vi.mock("@/hooks/use-saved-jobs", () => ({
  useSavedJobs: () => ({ isSaved: () => false, save: vi.fn(), remove: vi.fn() }),
}));

vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({ lang: "en", dir: "ltr" }),
}));

vi.mock("@/hooks/use-seo", () => ({
  usePageMeta: vi.fn(),
}));

// Jobs renders inside <Layout> (navbar/footer use useAuth); mock the shell chrome.
vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ isAuthenticated: false, user: null }),
}));

vi.mock("@/components/Layout", () => ({
  Layout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockJobs = [
  {
    id: 1,
    uuid: "uuid-1",
    title: "Senior Frontend Developer",
    slug: "senior-frontend-developer",
    company_name: "Tech Corp",
    location: "Remote",
    location_type: "remote",
    posted_at: "2024-01-01T00:00:00Z",
    posted_ago: "2 days ago",
    status: "active",
    is_saved: false,
  },
  {
    id: 2,
    uuid: "uuid-2",
    title: "Backend Engineer",
    slug: "backend-engineer",
    company_name: "Data Inc",
    location: "New York, NY",
    location_type: "onsite",
    posted_at: "2024-01-02T00:00:00Z",
    posted_ago: "1 day ago",
    status: "active",
    is_saved: true,
  },
];

const renderJobs = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/app/jobs"]}>
        <Jobs />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("Jobs Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a loading state initially", () => {
    mocks.fetchJobs.mockImplementation(() => new Promise(() => {}));
    renderJobs();
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders the job list when data loads", async () => {
    mocks.fetchJobs.mockResolvedValue({ count: 2, results: mockJobs });
    renderJobs();

    await waitFor(() => {
      expect(screen.getByText("Senior Frontend Developer")).toBeInTheDocument();
      expect(screen.getByText("Backend Engineer")).toBeInTheDocument();
    });
  });

  it("shows an empty state when there are no results", async () => {
    mocks.fetchJobs.mockResolvedValue({ count: 0, results: [] });
    renderJobs();

    await waitFor(() => {
      expect(screen.getByText(/No jobs match your filters/i)).toBeInTheDocument();
    });
  });

  it("shows a retryable error state when the request fails", async () => {
    mocks.fetchJobs.mockRejectedValue(new Error("Network error"));
    renderJobs();

    await waitFor(() => {
      expect(screen.getByText(/Couldn't load jobs/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Try again/i })).toBeInTheDocument();
    });
  });

  it("renders pagination controls when there are multiple pages", async () => {
    mocks.fetchJobs.mockResolvedValue({ count: 20, results: mockJobs });
    renderJobs();

    await waitFor(() => {
      expect(screen.getByText("Next")).toBeInTheDocument();
    });
  });
});
