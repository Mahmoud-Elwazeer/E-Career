/**
 * Scores service for talent scoring and career intelligence
 */

import api from './api';

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
  /**
   * Get all talent scores for the authenticated user
   */
  getScores: async (): Promise<{ success: boolean; data: TalentScore }> => {
    const response = await api.get('/career/scores/');
    return response.data;
  },

  /**
   * Get detailed breakdown for a specific score dimension
   */
  getScoreBreakdown: async (dimension: string): Promise<{ success: boolean; data: ScoreBreakdown }> => {
    const response = await api.get(`/career/scores/breakdown/${dimension}/`);
    return response.data;
  },

  /**
   * Get score trends over time
   */
  getScoreTrends: async (): Promise<{ success: boolean; data: ScoreTrendsResponse }> => {
    const response = await api.get('/career/scores/trends/');
    return response.data;
  },

  /**
   * Trigger recalculation of all talent scores
   */
  recalculateScores: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/career/scores/recalculate/');
    return response.data;
  },

  /**
   * Get all scores with recommended actions
   */
  getAllScoresWithActions: async (): Promise<{ success: boolean; data: AllScoresWithActions }> => {
    const response = await api.get('/career/scores/with-actions/');
    return response.data;
  },

  /**
   * Get composite career score
   */
  getCompositeScore: async (): Promise<{ overall_score: number; overall_grade: string; dimensions: { [key: string]: number } }> => {
    const response = await api.get('/career/scores/');
    if (response.data.success) {
      const data = response.data.data;
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
    }
    throw new Error('Failed to get composite score');
  },
};

/**
 * Calculate letter grade from score
 */
export const calculateGrade = (score: number): string => {
  if (score >= 0.8) return 'A';
  if (score >= 0.65) return 'B';
  if (score >= 0.5) return 'C';
  if (score >= 0.35) return 'D';
  return 'F';
};

/**
 * Get color for grade
 */
export const getGradeColor = (grade: string): string => {
  const colors: { [key: string]: string } = {
    A: '#10b981', // emerald-500
    B: '#3b82f6', // blue-500
    C: '#f59e0b', // amber-500
    D: '#f97316', // orange-500
    F: '#ef4444', // red-500
  };
  return colors[grade] || '#6b7280'; // gray-500
};

/**
 * Get trend color
 */
export const getTrendColor = (trend: string): string => {
  const colors: { [key: string]: string } = {
    improving: '#10b981', // emerald-500
    stable: '#6b7280', // gray-500
    declining: '#ef4444', // red-500
  };
  return colors[trend] || '#6b7280';
};

export default scoresApi;