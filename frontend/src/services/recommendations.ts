/**
 * Recommendations API service
 */

import { apiRequest } from './client';

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
