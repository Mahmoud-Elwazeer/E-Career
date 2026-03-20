import { apiRequest } from "./client";

export interface Company {
  id: number;
  uuid: string;
  name: string;
  slug: string;
  logo_url: string;
  snippet: string;
  about: string;
  industry: string;
  website: string;
  is_active: boolean;
}

export interface Source {
  id: number;
  uuid: string;
  name: string;
  slug: string;
  url: string;
  logo_url: string;
  type: string;
  is_active: boolean;
}

export interface Tag {
  id: number;
  uuid: string;
  name: string;
  slug: string;
  category: string;
}

export interface Job {
  id: number;
  uuid: string;
  title: string;
  slug: string;
  company_name: string;
  company_logo: string;
  company_slug: string;
  location: string;
  location_type: "remote" | "onsite" | "hybrid";
  industry: string;
  experience_level: "entry" | "mid" | "senior" | "lead";
  description?: string;
  tags: Tag[];
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  source_name?: string;
  source_logo?: string;
  source_url: string;
  posted_at: string;
  deadline?: string;
  status: string;
  is_saved: boolean;
  company?: Company;
  source?: Source;
  also_on_sources?: Source[];
  view_count?: number;
  click_count?: number;
}

export interface PaginatedJobs {
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
  results: Job[];
}

export interface FetchJobsParams {
  q?: string;
  work_mode?: string;
  industry?: string;
  seniority?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export async function fetchJobs(params: FetchJobsParams = {}): Promise<PaginatedJobs> {
  return apiRequest<PaginatedJobs>("/jobs/", {
    auth: false,
    params: params as Record<string, string | number | boolean | undefined>,
  });
}

export async function fetchJobBySlug(slug: string): Promise<Job> {
  return apiRequest<Job>(`/jobs/${slug}/`, { auth: false });
}

export async function fetchSimilarJobs(slug: string): Promise<Job[]> {
  return apiRequest<Job[]>(`/jobs/${slug}/similar/`, { auth: false });
}

export async function logApplyClick(slug: string): Promise<{ source_url: string }> {
  return apiRequest<{ source_url: string }>(`/jobs/${slug}/apply/`, {
    method: "POST",
    auth: false,
  });
}

export async function fetchCompanies(): Promise<Company[]> {
  const data = await apiRequest<any>("/jobs/companies/", { auth: false });
  // Handle both paginated and non-paginated responses
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function fetchCompanyBySlug(slug: string): Promise<Company> {
  return apiRequest<Company>(`/jobs/companies/${slug}/`, { auth: false });
}

export async function fetchSources(): Promise<Source[]> {
  const data = await apiRequest<any>("/jobs/sources/", { auth: false });
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function fetchTags(): Promise<Tag[]> {
  const data = await apiRequest<any>("/jobs/tags/", { auth: false });
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}
