/**
 * Profile service for user profile management
 */

import api from './api';

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
   * Get current user's profile
   */
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/profile/');
    return response.data;
  },

  /**
   * Update profile
   */
  updateProfile: async (data: UpdateProfileData): Promise<UserProfile> => {
    const response = await api.patch('/profile/', data);
    return response.data;
  },

  /**
   * Upload CV file
   */
  uploadCV: async (file: File): Promise<{ status: string; message: string; profile: UserProfile }> => {
    const formData = new FormData();
    formData.append('cv_file', file);

    const response = await api.post('/profile/upload_cv/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Get profile completion status
   */
  getCompletion: async (): Promise<ProfileCompletion> => {
    const response = await api.get('/profile/completion/');
    return response.data;
  },

  /**
   * Update skills manually
   */
  updateSkills: async (skills: string[]): Promise<{ status: string; skills: string[] }> => {
    const response = await api.post('/profile/skills/', { skills });
    return response.data;
  },

  /**
   * Update job preferences
   */
  updatePreferences: async (data: UpdatePreferencesData): Promise<UserProfile> => {
    const response = await api.post('/profile/preferences/', data);
    return response.data;
  },

  /**
   * Get job matches
   */
  getMatches: async (limit = 20, minScore = 50): Promise<JobMatch[]> => {
    const response = await api.get('/profile/matches/', {
      params: { limit, min_score: minScore },
    });
    return response.data;
  },

  /**
   * Calculate match scores
   */
  calculateMatches: async (): Promise<{ status: string; matches_calculated: number }> => {
    const response = await api.post('/profile/calculate_matches/');
    return response.data;
  },
};

export default profileApi;