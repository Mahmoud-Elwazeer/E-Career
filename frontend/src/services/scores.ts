/**
 * Scores service for talent scoring and career intelligence
 */

import { apiRequest } from './client';

// Types
export interface ScoreBreakdown {
  value: number;
  confidence: number;
  grade: string;
  trend: 'improving' | 'stable' | 'declining';
  evidence: Array<{
    type: string;
    count?: number;
    description: string;
    score?: number;
  }>;
  explanation: string;
  actions: Array<{
    type: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  breakdown: {
    [key: string]: number;
  };
}

export interface TalentScore {
  id: number;
  user_email: string;
  overall_score: number;
  skill_score: number;
  experience_score: number;
  education_score: number;
  portfolio_score: number;
  interview_score: number;
  growth_score: number;
  communication_score: number;
  ai_confidence: number;
  explanations: {
    [key: string]: {
      evidence: any[];
      explanation: string;
      actions: any[];
      trend: string;
    };
  };
  score_history: Array<{
    date: string;
    overall_score: number;
    dimensions: {
      [key: string]: number;
    };
  }>;
  last_calculated_at: string;
  dimension_breakdown: {
    skill_score: number;
    experience_score: number;
    education_score: number;
    portfolio_score: number;
    interview_score: number;
    growth_score: number;
    communication_score: number;
  };
}

export interface ScoreTrend {
  dimension: string;
  current_value: number;
  previous_value: number;
  change: number;
  direction: 'improving' | 'stable' | 'declining';
}

export interface ScoreTrendsResponse {
  trends: Array<{
    date: string;
    overall_score: number;
    dimensions: {
      [key: string]: number;
    };
  }>;
  current_scores: {
    [key: string]: number;
  };
  trend_direction: 'improving' | 'stable' | 'declining' | 'insufficient_data';
  dimension_trends: ScoreTrend[];
}

export interface AllScoresWithActions {
  overall_score: number;
  overall_grade: string;
  dimensions: {
    [key: string]: ScoreBreakdown;
  };
  explanations: {
    [key: string]: {
      evidence: any[];
      explanation: string;
      actions: any[];
      trend: string;
    };
  };
  actions: Array<{
    dimension: string;
    type: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
  }>;
  confidence: number;
}

// Scores API functions
export const scoresApi = {
  getScores: async (): Promise<TalentScore> => {
    return apiRequest<TalentScore>('/career/scores/');
  },

  getScoreBreakdown: async (dimension: string): Promise<ScoreBreakdown> => {
    return apiRequest<ScoreBreakdown>(`/career/scores/breakdown/${dimension}/`);
  },

  getScoreTrends: async (): Promise<ScoreTrendsResponse> => {
    return apiRequest<ScoreTrendsResponse>('/career/scores/trends/');
  },

  recalculateScores: async (): Promise<{ success: boolean; message: string }> => {
    return apiRequest<{ success: boolean; message: string }>('/career/scores/recalculate/', {
      method: 'POST'
    });
  },

  getAllScoresWithActions: async (): Promise<AllScoresWithActions> => {
    return apiRequest<AllScoresWithActions>('/career/scores/with-actions/');
  },

  getCompositeScore: async (): Promise<{ overall_score: number; overall_grade: string; dimensions: { [key: string]: number } }> => {
    const data = await apiRequest<TalentScore>('/career/scores/');
    return {
      overall_score: data.overall_score,
      overall_grade: calculateGrade(data.overall_score),
      dimensions: {
        skill_score: data.skill_score,
        experience_score: data.experience_score,
        education_score: data.education_score,
        portfolio_score: data.portfolio_score,
        interview_score: data.interview_score,
        growth_score: data.growth_score,
        communication_score: data.communication_score,
      },
    };
  },
};

export const calculateGrade = (score: number): string => {
  if (score >= 0.8) return 'A';
  if (score >= 0.65) return 'B';
  if (score >= 0.5) return 'C';
  if (score >= 0.35) return 'D';
  return 'F';
};

export const getGradeColor = (grade: string): string => {
  const colors: { [key: string]: string } = {
    A: '#10b981',
    B: '#3b82f6',
    C: '#f59e0b',
    D: '#f97316',
    F: '#ef4444',
  };
  return colors[grade] || '#6b7280';
};

export const getTrendColor = (trend: string): string => {
  const colors: { [key: string]: string } = {
    improving: '#10b981',
    stable: '#6b7280',
    declining: '#ef4444',
  };
  return colors[trend] || '#6b7280';
};

export default scoresApi;
