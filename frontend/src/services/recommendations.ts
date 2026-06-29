/**
 * Recommendations API service
 */

import api from './api';

export interface RecommendedJob {
  job: {
    id: number;
    title: string;
    company: {
      id: number;
      name: string;
      logo?: string;
    };
    location: string;
    location_type?: string;
    salary_min?: number;
    salary_max?: number;
    posted_date: string;
    employment_type?: string;
  };
  match_score: number;
  reasoning: string;
}

export interface RecommendationsResponse {
  count: number;
  recommendations: RecommendedJob[];
}

export interface MatchBreakdown {
  overall_score: number;
  breakdown: {
    [key: string]: {
      score: number;
      reasoning: string;
    };
  };
  strengths: string[];
  gaps: string[];
  recommendation: string;
  improvement_tips: string[];
}

export interface SimilarJobsResponse {
  count: number;
  jobs: Array<{
    id: number;
    title: string;
    company: {
      id: number;
      name: string;
      logo?: string;
    };
    location: string;
    posted_date: string;
  }>;
}

/**
 * Get personalized job recommendations
 */
export async function getRecommendations(
  limit: number = 20,
  minScore: number = 60
): Promise<RecommendationsResponse> {
  const response = await api.get('/recommendations/', {
    params: { limit, min_score: minScore }
  });
  return response.data;
}

/**
 * Get detailed match breakdown for a specific job
 */
export async function getMatchBreakdown(jobId: number): Promise<MatchBreakdown> {
  const response = await api.get(`/jobs/${jobId}/match-breakdown/`);
  return response.data;
}

/**
 * Get similar jobs to a specific job
 */
export async function getSimilarJobs(jobId: number): Promise<SimilarJobsResponse> {
  const response = await api.get(`/jobs/${jobId}/similar/`);
  return response.data;
}

const recommendationsService = {
  getRecommendations,
  getMatchBreakdown,
  getSimilarJobs,
};

export default recommendationsService;