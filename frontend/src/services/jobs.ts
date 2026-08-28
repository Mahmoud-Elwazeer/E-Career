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

export interface MatchBreakdown {
  overall_score: number;
  components: {
    skills?: {
      score: number;
      matched: string[];
      missing: string[];
    };
    location?: {
      score: number;
      user_preference: string[] | null;
      job_location: string;
    };
    experience?: {
      user_years: number | null;
      job_requirement: string;
    };
    salary?: {
      user_expectation: number | null;
      job_offer_min: number | null;
      job_offer_max: number | null;
    };
  };
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
  salary_display?: string;
  source_name?: string;
  source_logo?: string;
  source_url: string;
  direct_apply_url?: string;
  apply_url_verified?: boolean;
  posted_at: string;
  posted_ago?: string;
  deadline?: string;
  status: string;
  is_saved: boolean;
  match_score?: number;
  match_breakdown?: MatchBreakdown;
  similar_jobs?: Job[];
  employment_type?: string;
  legitimacy_score?: number;
  legitimacy_flags?: string[];
  company?: Company;
  source?: Source;
  also_on_sources?: Source[];
  view_count?: number;
  click_count?: number;
  custom_form_fields?: Array<{
    id: string;
    type: 'text' | 'textarea' | 'select' | 'multiselect' | 'yes_no' | 'number' | 'date' | 'url';
    label: string;
    required: boolean;
    placeholder?: string;
    options?: string[];
    validation?: { min_length?: number; max_length?: number; pattern?: string };
    knockout_value?: string;
  }>;
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

// Phase 1C: Save/Unsave job
export async function saveJob(slug: string): Promise<{ is_saved: boolean }> {
  return apiRequest<{ is_saved: boolean }>(`/jobs/${slug}/save/`, {
    method: "POST",
    auth: true,
  });
}

export async function unsaveJob(slug: string): Promise<{ is_saved: boolean }> {
  return apiRequest<{ is_saved: boolean }>(`/jobs/${slug}/unsave/`, {
    method: "POST",
    auth: true,
  });
}

// Phase 1C: Ask Rashid about a job (Phase 2B integration)
export async function askRashidAboutJob(slug: string): Promise<{
  message: string;
  job_id: number;
  job_title: string;
  company: string;
  location: string;
  salary_range: string | null;
  skills_required: string[];
}> {
  return apiRequest(`/jobs/${slug}/ask-rashid/`, { auth: true });
}

// Feature 2: Submit application with custom form responses
export async function submitApplication(slug: string, data: {
  custom_form_responses: Record<string, any>;
  cv_file?: File;
}): Promise<{
  application_id: number;
  status: string;
  applied_at: string;
  knockout_reason?: string;
  knockout_results?: Array<{ field_id: string; field_label: string; user_answer: string; knockout_value: string }>;
}> {
  if (data.cv_file) {
    const formData = new FormData();
    formData.append("custom_form_responses", JSON.stringify(data.custom_form_responses));
    formData.append("cv_file", data.cv_file);
    return apiRequest(`/jobs/${slug}/submit-application/`, {
      method: "POST",
      formData,
      auth: true,
    });
  }
  return apiRequest(`/jobs/${slug}/submit-application/`, {
    method: "POST",
    body: { custom_form_responses: data.custom_form_responses },
    auth: true,
  });
}
