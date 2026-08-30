import { apiRequest } from './client';

// 5.2: Resume Tailoring
export interface TailorResult {
  original_score: number;
  tailored_score: number;
  score_delta: number;
  suggestions: string[];
  missing_skills: string[];
  skill_match_ratio: number;
  tailored_resume_preview: string | null;
  original_ats_breakdown: Record<string, number>;
  tailored_ats_breakdown: Record<string, number>;
}

export async function tailorResume(jobId: number): Promise<TailorResult> {
  return apiRequest<TailorResult>(`/career/jobs/${jobId}/tailor/`, {
    method: 'POST',
  });
}

// 5.5: Insider Connections
export interface InsiderConnection {
  user_id: number;
  name: string;
  current_role: string;
  current_company: string;
  connection_type: 'current_employee' | 'former_employee';
  experience_years: number;
}

export interface GitHubContributor {
  username: string;
  profile_url: string;
  avatar_url: string;
  source: string;
}

export interface ConnectionsResult {
  company: { id: number; name: string; slug: string };
  ecareer_connections: InsiderConnection[];
  github_contributors: GitHubContributor[];
  total_connections: number;
}

export async function getInsiderConnections(companyId: number): Promise<ConnectionsResult> {
  return apiRequest<ConnectionsResult>(`/employer/connections/${companyId}/`);
}

// 5.3: Quick Apply
export interface QuickApplyData {
  ats_provider: string;
  can_auto_submit: boolean;
  prepared_data: {
    full_name: string;
    email: string;
    phone: string;
    resume_url: string | null;
    linkedin_url: string | null;
    portfolio_url: string | null;
    current_company: string;
    current_title: string;
  };
  apply_url: string;
  provider_info: {
    name: string;
    supported: boolean;
    can_auto_submit: boolean;
    note: string;
  };
}

export async function prepareQuickApply(jobId: string): Promise<QuickApplyData> {
  return apiRequest<QuickApplyData>(`/employer/quick-apply/${jobId}/prepare/`);
}

export async function recordQuickApply(jobId: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/employer/quick-apply/${jobId}/record/`, {
    method: 'POST',
  });
}
