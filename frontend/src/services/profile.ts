/**
 * Profile service for user profile management
 */

import { apiRequest } from './client';

// Types
export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  cv_file: string | null;
  cv_uploaded_at: string | null;
  cv_parse_status: 'pending' | 'processing' | 'done' | 'failed';
  portfolio_url: string;
  skills: string[];
  experience_years: number;
  education: EducationItem[];
  languages: LanguageItem[];
  certifications: CertificationItem[];
  current_role: string;
  desired_roles: string[];
  desired_locations: string[];
  preferred_type: string;
  open_to_remote: boolean;
  min_salary: number | null;
  salary_currency: string;
  email_alerts: boolean;
  alert_frequency: 'instant' | 'daily' | 'weekly';
  min_match_score: number;
  completion_percentage: number;
  is_complete: boolean;
  created_at: string;
  updated_at: string;
}

export interface EducationItem {
  degree: string;
  institution: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  gpa?: string;
}

export interface LanguageItem {
  language: string;
  level: string;
}

export interface CertificationItem {
  name: string;
  issuer: string;
  date?: string;
  credential_id?: string;
}

export interface ProfileCompletion {
  total_score: number;
  is_complete: boolean;
  sections: {
    [key: string]: {
      complete: boolean;
      weight: number;
      label: string;
    };
  };
}

export interface JobMatch {
  id: number;
  job: number;
  job_title: string;
  company_name: string;
  job_slug: string;
  score: number;
  breakdown: {
    [key: string]: {
      score: number;
      reasoning?: string;
    };
  };
  calculated_at: string;
}

export interface UpdateProfileData {
  portfolio_url?: string;
  desired_roles?: string[];
  desired_locations?: string[];
  preferred_type?: string;
  open_to_remote?: boolean;
  min_salary?: number | null;
  salary_currency?: string;
  email_alerts?: boolean;
  alert_frequency?: 'instant' | 'daily' | 'weekly';
  min_match_score?: number;
}

export interface UpdateSkillsData {
  skills: string[];
}

export interface UpdatePreferencesData {
  desired_roles?: string[];
  desired_locations?: string[];
  preferred_type?: string;
  open_to_remote?: boolean;
  min_salary?: number | null;
  salary_currency?: string;
}

// Profile API functions
export const profileApi = {
  /**
   * Get current user's profile.
   * The app is mounted at /profile/ and the DRF router registers the ViewSet
   * under `profile`, so the real collection URL is /profile/profile/ (the
   * ViewSet.list() returns the current user's own profile).
   */
  getProfile: async (): Promise<UserProfile> => {
    return apiRequest<UserProfile>('/profile/profile/');
  },

  /**
   * Update profile. DRF maps update/partial_update to the detail route
   * (/profile/profile/{id}/); the ViewSet resolves the object to the current
   * user regardless of id, so we pass the loaded profile id.
   */
  updateProfile: async (id: number, data: UpdateProfileData): Promise<UserProfile> => {
    return apiRequest<UserProfile>(`/profile/profile/${id}/`, {
      method: 'PATCH',
      body: data,
    });
  },

  /**
   * Upload CV file (detail=False action -> /profile/profile/upload_cv/)
   */
  uploadCV: async (file: File): Promise<{ status: string; message: string; profile: UserProfile }> => {
    const formData = new FormData();
    formData.append('cv_file', file);

    return apiRequest<{ status: string; message: string; profile: UserProfile }>('/profile/profile/upload_cv/', {
      method: 'POST',
      formData,
    });
  },

  /**
   * Get profile completion status
   */
  getCompletion: async (): Promise<ProfileCompletion> => {
    return apiRequest<ProfileCompletion>('/profile/profile/completion/');
  },

  /**
   * Update skills manually
   */
  updateSkills: async (skills: string[]): Promise<{ status: string; skills: string[] }> => {
    return apiRequest<{ status: string; skills: string[] }>('/profile/profile/skills/', {
      method: 'POST',
      body: { skills },
    });
  },

  /**
   * Update job preferences
   */
  updatePreferences: async (data: UpdatePreferencesData): Promise<UserProfile> => {
    return apiRequest<UserProfile>('/profile/profile/preferences/', {
      method: 'POST',
      body: data,
    });
  },

  /**
   * Get job matches (JobMatchViewSet is registered at `matches` -> /profile/matches/)
   */
  getMatches: async (limit = 20, minScore = 50): Promise<JobMatch[]> => {
    return apiRequest<JobMatch[]>('/profile/profile/matches/', {
      params: { limit, min_score: minScore },
    });
  },

  /**
   * Calculate match scores
   */
  calculateMatches: async (): Promise<{ status: string; matches_calculated: number }> => {
    return apiRequest<{ status: string; matches_calculated: number }>('/profile/profile/calculate_matches/', {
      method: 'POST',
    });
  },
};

export default profileApi;
