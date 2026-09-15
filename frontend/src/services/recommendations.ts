/**
 * Recommendations API service
 */

import { apiRequest } from './client';

/**
 * Flat recommendation shape returned by the backend recommendation engine
 * (apps/search/recommendation_engine.get_recommendations). Explainability
 * fields (match_reasons / explanation / match_factors) are always present.
 */
export interface RecommendedJob {
  job_id: string;
  job_title: string;
  company_name: string;
  location: string;
  score: number;
  collaborative_score?: number;
  content_score?: number;
  employment_type?: string;
  work_arrangement?: string;
  salary_min?: number | null;
  salary_max?: number | null;
  match_reasons?: string[];
  explanation?: string;
  match_factors?: Record<string, unknown>;
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

export async function getRecommendations(
  limit: number = 20,
  minScore: number = 60
): Promise<RecommendationsResponse> {
  return apiRequest<RecommendationsResponse>('/career/recommendations/', {
    params: { limit: limit, min_score: minScore }
  });
}

export async function getMatchBreakdown(jobId: string): Promise<MatchBreakdown> {
  return apiRequest<MatchBreakdown>(`/career/jobs/${jobId}/match-breakdown/`);
}

export async function getSimilarJobs(jobId: number): Promise<SimilarJobsResponse> {
  return apiRequest<SimilarJobsResponse>(`/career/jobs/${jobId}/similar/`);
}

const recommendationsService = {
  getRecommendations,
  getMatchBreakdown,
  getSimilarJobs,
};

export default recommendationsService;
