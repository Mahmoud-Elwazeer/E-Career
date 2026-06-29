/**
 * Employer API Service
 * Phase 3A: Employer Portal
 */
import api from './api';

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
  const response = await api.get('/api/v1/employer/profile/');
  return response.data;
};

export const createEmployerProfile = async (data: {
  company_id: number;
  job_title: string;
  phone?: string;
}): Promise<{ message: string; employer: EmployerProfile }> => {
  const response = await api.post('/api/v1/employer/register/', data);
  return response.data;
};

export const updateEmployerProfile = async (data: {
  job_title?: string;
  phone?: string;
}): Promise<EmployerProfile> => {
  const response = await api.put('/api/v1/employer/profile/', data);
  return response.data;
};

export const requestVerification = async (): Promise<{ message: string; status: string }> => {
  const response = await api.post('/api/v1/employer/profile/request_verification/');
  return response.data;
};

export const getEmployerStats = async (): Promise<EmployerStats> => {
  const response = await api.get('/api/v1/employer/profile/stats/');
  return response.data;
};

// Company Search
export const searchCompanies = async (query: string): Promise<{ companies: Company[] }> => {
  const response = await api.get('/api/v1/employer/companies/search/', {
    params: { q: query }
  });
  return response.data;
};

// Job Posting APIs
export const getJobPostings = async (): Promise<JobPosting[]> => {
  const response = await api.get('/api/v1/employer/jobs/');
  return response.data;
};

export const getJobPosting = async (id: number): Promise<JobPosting> => {
  const response = await api.get(`/api/v1/employer/jobs/${id}/`);
  return response.data;
};

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
}

export const createJobPosting = async (data: CreateJobPostingData): Promise<JobPosting> => {
  const response = await api.post('/api/v1/employer/jobs/', data);
  return response.data;
};

export const updateJobPosting = async (id: number, data: Partial<CreateJobPostingData>): Promise<JobPosting> => {
  const response = await api.put(`/api/v1/employer/jobs/${id}/`, data);
  return response.data;
};

export const deleteJobPosting = async (id: number): Promise<void> => {
  await api.delete(`/api/v1/employer/jobs/${id}/`);
};

export const publishJobPosting = async (id: number): Promise<{ message: string; status: string }> => {
  const response = await api.post(`/api/v1/employer/jobs/${id}/publish/`);
  return response.data;
};

export const closeJobPosting = async (id: number): Promise<{ message: string; status: string }> => {
  const response = await api.post(`/api/v1/employer/jobs/${id}/close/`);
  return response.data;
};

export const reopenJobPosting = async (id: number): Promise<{ message: string; status: string }> => {
  const response = await api.post(`/api/v1/employer/jobs/${id}/reopen/`);
  return response.data;
};

export const getJobApplicants = async (jobId: number): Promise<{
  job_title: string;
  total_applicants: number;
  applicants: JobApplication[];
}> => {
  const response = await api.get(`/api/v1/employer/jobs/${jobId}/applicants/`);
  return response.data;
};

// Application Management APIs
export const getApplications = async (filters?: {
  status?: string;
  job_id?: number;
}): Promise<JobApplication[]> => {
  const response = await api.get('/api/v1/employer/applications/', {
    params: filters
  });
  return response.data;
};

export const getApplication = async (id: number): Promise<JobApplication> => {
  const response = await api.get(`/api/v1/employer/applications/${id}/`);
  return response.data;
};

export const updateApplicationStatus = async (id: number, status: string): Promise<JobApplication> => {
  const response = await api.patch(`/api/v1/employer/applications/${id}/`, { status });
  return response.data;
};

export const shortlistApplication = async (id: number): Promise<{ message: string; status: string }> => {
  const response = await api.post(`/api/v1/employer/applications/${id}/shortlist/`);
  return response.data;
};

export const rejectApplication = async (id: number): Promise<{ message: string; status: string }> => {
  const response = await api.post(`/api/v1/employer/applications/${id}/reject/`);
  return response.data;
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
};