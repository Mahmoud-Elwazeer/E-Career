/**
 * Employer API Service
 * Phase 3A: Employer Portal
 */
import { apiRequest } from './client';

// Types
export interface EmployerProfile {
  id: number;
  user_email: string;
  user_name: string;
  company: {
    id: number;
    name: string;
    logo_url: string;
    website: string;
    industry: string;
  };
  job_title: string;
  phone: string;
  is_verified: boolean;
  verified_at: string | null;
  created_at: string;
}

export interface JobPosting {
  id: number;
  uuid: string;
  title: string;
  company_name: string;
  company_logo: string;
  location: string;
  employment_type: string;
  employment_type_display: string;
  remote_type: string;
  remote_type_display: string;
  experience_level: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_display: string | null;
  status: string;
  status_display: string;
  published_at: string | null;
  expires_at: string | null;
  views_count: number;
  clicks_count: number;
  applications_count: number;
  created_at: string;
  updated_at: string;
  description?: string;
  requirements?: string;
  apply_url?: string;
  apply_url_verified?: boolean;
  rejected_reason?: string;
}

export interface JobApplication {
  id: number;
  user_name: string;
  user_email: string;
  job_title: string;
  job_id: number;
  status: string;
  status_display: string;
  cv_url: string | null;
  applied_at: string;
  user_phone?: string;
  user_profile?: {
    current_position: string;
    years_of_experience: number;
    location: string;
    skills: string[];
  };
}

export interface EmployerStats {
  jobs: {
    total_jobs: number;
    active_jobs: number;
    draft_jobs: number;
    pending_jobs: number;
  };
  applications: {
    total_applications: number;
    new_applications: number;
    viewed_applications: number;
    shortlisted: number;
    rejected: number;
  };
  engagement: {
    total_views: number;
    total_clicks: number;
  };
  is_verified: boolean;
}

export interface Company {
  id: number;
  name: string;
  website: string;
  industry: string;
}

// Employer Profile APIs
export const getEmployerProfile = async (): Promise<EmployerProfile> => {
  return apiRequest<EmployerProfile>('/employer/profile/');
};

export const createEmployerProfile = async (data: {
  company_id: number;
  job_title: string;
  phone?: string;
}): Promise<{ message: string; employer: EmployerProfile }> => {
  return apiRequest('/employer/register/', { method: 'POST', body: data });
};

export const updateEmployerProfile = async (data: {
  job_title?: string;
  phone?: string;
}): Promise<EmployerProfile> => {
  return apiRequest('/employer/profile/', { method: 'PUT', body: data });
};

export const requestVerification = async (): Promise<{ message: string; status: string }> => {
  return apiRequest('/employer/profile/request_verification/', { method: 'POST' });
};

export const getEmployerStats = async (): Promise<EmployerStats> => {
  return apiRequest<EmployerStats>('/employer/profile/stats/');
};

// Company Search
export const searchCompanies = async (query: string): Promise<{ companies: Company[] }> => {
  return apiRequest('/employer/companies/search/', { params: { q: query } });
};

// Job Posting APIs
export const getJobPostings = async (): Promise<JobPosting[]> => {
  return apiRequest<JobPosting[]>('/employer/jobs/');
};

export const getJobPosting = async (id: number): Promise<JobPosting> => {
  return apiRequest<JobPosting>(`/employer/jobs/${id}/`);
};

export interface CustomFormField {
  id: string;
  type: 'text' | 'textarea' | 'select' | 'multiselect' | 'yes_no' | 'number' | 'date' | 'url';
  label: string;
  required: boolean;
  placeholder?: string;
  options?: string[];
  validation?: {
    min_length?: number;
    max_length?: number;
    pattern?: string;
  };
  knockout_value?: string;
}

export interface CreateJobPostingData {
  title: string;
  description: string;
  requirements: string;
  employment_type: string;
  experience_level: string;
  remote_type: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  apply_url: string;
  custom_form_fields?: CustomFormField[];
}

export const createJobPosting = async (data: CreateJobPostingData): Promise<JobPosting> => {
  return apiRequest<JobPosting>('/employer/jobs/', { method: 'POST', body: data });
};

export const updateJobPosting = async (id: number, data: Partial<CreateJobPostingData>): Promise<JobPosting> => {
  return apiRequest<JobPosting>(`/employer/jobs/${id}/`, { method: 'PUT', body: data });
};

export const deleteJobPosting = async (id: number): Promise<void> => {
  return apiRequest(`/employer/jobs/${id}/`, { method: 'DELETE' });
};

export const publishJobPosting = async (id: number): Promise<{ message: string; status: string }> => {
  return apiRequest(`/employer/jobs/${id}/publish/`, { method: 'POST' });
};

export const closeJobPosting = async (id: number): Promise<{ message: string; status: string }> => {
  return apiRequest(`/employer/jobs/${id}/close/`, { method: 'POST' });
};

export const reopenJobPosting = async (id: number): Promise<{ message: string; status: string }> => {
  return apiRequest(`/employer/jobs/${id}/reopen/`, { method: 'POST' });
};

export const getJobApplicants = async (jobId: number): Promise<{
  job_title: string;
  total_applicants: number;
  applicants: JobApplication[];
}> => {
  return apiRequest(`/employer/jobs/${jobId}/applicants/`);
};

// Application Management APIs
export const getApplications = async (filters?: {
  status?: string;
  job_id?: number;
}): Promise<JobApplication[]> => {
  return apiRequest<JobApplication[]>('/employer/applications/', { params: filters as any });
};

export const getApplication = async (id: number): Promise<JobApplication> => {
  return apiRequest<JobApplication>(`/employer/applications/${id}/`);
};

export const updateApplicationStatus = async (id: number, status: string): Promise<JobApplication> => {
  return apiRequest<JobApplication>(`/employer/applications/${id}/`, { method: 'PATCH', body: { status } });
};

export const shortlistApplication = async (id: number): Promise<{ message: string; status: string }> => {
  return apiRequest(`/employer/applications/${id}/shortlist/`, { method: 'POST' });
};

export const rejectApplication = async (id: number): Promise<{ message: string; status: string }> => {
  return apiRequest(`/employer/applications/${id}/reject/`, { method: 'POST' });
};

// Talent Pool Types
export interface TalentPool {
  id: number;
  name: string;
  description: string;
  candidate_count: number;
  created_at: string;
  updated_at: string;
}

export interface TalentPoolCandidate {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  tags: string[];
  notes: string;
  source: string;
  added_at: string;
}

export interface TalentPoolDetail extends TalentPool {
  candidates: TalentPoolCandidate[];
}

export interface CreateTalentPoolData {
  name: string;
  description?: string;
}

export interface AddCandidateData {
  user_id: number;
  tags?: string[];
  notes?: string;
  source?: string;
}

export interface CandidateRanking {
  id: number;
  job_title: string;
  user_name: string;
  user_email: string;
  overall_score: number;
  skill_match_score: number;
  experience_score: number;
  education_score: number;
  salary_expectation_score: number;
  knockout_passed: boolean;
  knockout_failures: string[];
  explanations: Record<string, string>;
  status: 'pending' | 'ranked' | 'shortlisted' | 'rejected';
}

// Talent Pool APIs
export const listTalentPools = async (): Promise<TalentPool[]> => {
  return apiRequest<TalentPool[]>('/employer/talent-pools/');
};

export const createTalentPool = async (data: CreateTalentPoolData): Promise<TalentPool> => {
  return apiRequest<TalentPool>('/employer/talent-pools/', { method: 'POST', body: data });
};

export const getTalentPoolDetail = async (id: number): Promise<TalentPoolDetail> => {
  return apiRequest<TalentPoolDetail>(`/employer/talent-pools/${id}/`);
};

export const addCandidateToPool = async (poolId: number, data: AddCandidateData): Promise<TalentPoolCandidate> => {
  return apiRequest<TalentPoolCandidate>(`/employer/talent-pools/${poolId}/add_candidate/`, { method: 'POST', body: data });
};

export const rankCandidates = async (jobId: number, candidateIds?: number[], rankAll?: boolean): Promise<CandidateRanking[]> => {
  return apiRequest<CandidateRanking[]>('/employer/rankings/rank/', {
    method: 'POST',
    body: { job_id: jobId, candidate_ids: candidateIds, rank_all: rankAll },
  });
};

export const listRankings = async (jobId?: number): Promise<CandidateRanking[]> => {
  return apiRequest<CandidateRanking[]>('/employer/rankings/', {
    params: jobId ? { job_id: jobId } : undefined,
  });
};

// Export all as named exports
export default {
  // Profile
  getEmployerProfile,
  createEmployerProfile,
  updateEmployerProfile,
  requestVerification,
  getEmployerStats,
  searchCompanies,
  // Jobs
  getJobPostings,
  getJobPosting,
  createJobPosting,
  updateJobPosting,
  deleteJobPosting,
  publishJobPosting,
  closeJobPosting,
  reopenJobPosting,
  getJobApplicants,
  // Applications
  getApplications,
  getApplication,
  updateApplicationStatus,
  shortlistApplication,
  rejectApplication,
  // Talent Pools
  listTalentPools,
  createTalentPool,
  getTalentPoolDetail,
  addCandidateToPool,
  rankCandidates,
  listRankings,
};