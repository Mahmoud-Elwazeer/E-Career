/**
 * Jobs Page Tests
 * 
 * Tests for the Jobs page component including:
 * - Job list rendering
 * - Loading state handling
 * - Empty state handling
 * - Pagination
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Jobs from '../Jobs';

// Mock the jobs service
vi.mock('@/services/jobs', () => ({
  fetchJobs: vi.fn(),
}));

// Mock the useSavedJobs hook
vi.mock('@/hooks/use-saved-jobs', () => ({
  useSavedJobs: vi.fn(),
}));

// Mock the useTheme hook
vi.mock('@/hooks/use-theme', () => ({
  useTheme: vi.fn(),
}));

// Mock the usePageMeta hook
vi.mock('@/hooks/use-seo', () => ({
  usePageMeta: vi.fn(),
}));

// Mock the logSearch function
vi.mock('@/lib/api', () => ({
  logSearch: vi.fn(),
}));

// Import mocked hooks
const useTheme = vi.hoisted(() => vi.fn());
const useSavedJobs = vi.hoisted(() => vi.fn());
const fetchJobs = vi.hoisted(() => vi.fn());

describe('Jobs Page', () => {
  const mockJobs = [
    {
      id: 1,
      uuid: 'uuid-1',
      title: 'Senior Frontend Developer',
      slug: 'senior-frontend-developer',
      company_name: 'Tech Corp',
      company_logo: 'https://example.com/logo.png',
      company_slug: 'tech-corp',
      location: 'Remote',
      location_type: 'remote',
      industry: 'Technology',
      experience_level: 'senior',
      posted_at: '2024-01-01T00:00:00Z',
      posted_ago: '2 days ago',
      status: 'active',
      is_saved: false,
      match_score: 85,
      match_breakdown: {
        overall_score: 85,
        components: {
          skills: { score: 90, matched: ['React', 'TypeScript'], missing: ['AWS'] },
          location: { score: 100, user_preference: ['Remote'], job_location: 'Remote' },
          experience: { user_years: 5, job_requirement: '3-5 years' },
          salary: { user_expectation: 100000, job_offer_min: 90000, job_offer_max: 120000 },
        },
      },
    },
    {
      id: 2,
      uuid: 'uuid-2',
      title: 'Backend Engineer',
      slug: 'backend-engineer',
      company_name: 'Data Inc',
      company_logo: 'https://example.com/logo2.png',
      company_slug: 'data-inc',
      location: 'New York, NY',
      location_type: 'onsite',
      industry: 'Finance',
      experience_level: 'mid',
      posted_at: '2024-01-02T00:00:00Z',
      posted_ago: '1 day ago',
      status: 'active',
      is_saved: true,
    },
  ];

  const mockPaginatedJobs = {
    count: 2,
    total_pages: 1,
    current_page: 1,
    next: null,
    previous: null,
    results: mockJobs,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useTheme as any).mockReturnValue({ lang: 'en' });
    (useSavedJobs as any).mockReturnValue({ isSaved: () => false, save: vi.fn(), remove: vi.fn() });
  });

  it('renders loading state initially', async () => {
    (fetchJobs as any).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <MemoryRouter initialEntries={['/app/jobs']}>
        <Jobs />
      </MemoryRouter>
    );

    // Should show loading spinner
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders job list when data loads', async () => {
    (fetchJobs as any).mockResolvedValue(mockPaginatedJobs);

    render(
      <MemoryRouter initialEntries={['/app/jobs']}>
        <Jobs />
      </MemoryRouter>
    );

    // Wait for jobs to load
    await waitFor(() => {
      expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('Backend Engineer')).toBeInTheDocument();
      expect(screen.getByText('Data Inc')).toBeInTheDocument();
    });
  });

  it('handles empty state', async () => {
    (fetchJobs as any).mockResolvedValue({
      count: 0,
      total_pages: 0,
      current_page: 1,
      next: null,
      previous: null,
      results: [],
    });

    render(
      <MemoryRouter initialEntries={['/app/jobs']}>
        <Jobs />
      </MemoryRouter>
    );

    // Should show empty state
    await waitFor(() => {
      expect(screen.getByText(/No jobs match your filters/i)).toBeInTheDocument();
    });
  });

  it('handles error state', async () => {
    (fetchJobs as any).mockRejectedValue(new Error('Network error'));

    render(
      <MemoryRouter initialEntries={['/app/jobs']}>
        <Jobs />
      </MemoryRouter>
    );

    // Should show jobs list (even if empty) without crashing
    await waitFor(() => {
      expect(screen.getByText(/0 jobs found/i)).toBeInTheDocument();
    });
  });

  it('handles pagination', async () => {
    (fetchJobs as any).mockResolvedValue({
      count: 20,
      total_pages: 2,
      current_page: 1,
      next: '/api/v1/jobs/?page=2',
      previous: null,
      results: mockJobs,
    });

    render(
      <MemoryRouter initialEntries={['/app/jobs']}>
        <Jobs />
      </MemoryRouter>
    );

    // Should show pagination controls
    await waitFor(() => {
      expect(screen.getByText('Next')).toBeInTheDocument();
    });
  });
});