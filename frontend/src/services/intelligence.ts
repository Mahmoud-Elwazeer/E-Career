/**
 * Intelligence Layer API Service.
 *
 * Connects the frontend to the platform intelligence services:
 * - Rashid AI agent (Pydantic AI)
 * - Trend detection
 * - Research engine
 * - Email verification
 * - Tool registry
 */
import { apiRequest } from "./client";

// Types
export interface RashidResponse {
  response: string;
  model?: string;
  fallback?: boolean;
}

export interface EmergingSkill {
  skill: string;
  recent_count: number;
  previous_count: number;
  growth_pct: number;
  status: "emerging" | "growing";
}

export interface DecliningSkill {
  skill: string;
  recent_count: number;
  previous_count: number;
  decline_pct: number;
  status: "declining";
}

export interface ResearchTask {
  task_id: string;
  status: string;
  message: string;
}

export interface EmailVerificationResult {
  email: string;
  normalized: string;
  status: string;
  is_valid: boolean;
  is_disposable: boolean;
  has_mx_record: boolean;
  domain: string;
}

export interface PlatformTool {
  name: string;
  description: string;
}

export interface IntelligenceHealth {
  ai_service: {
    provider: string;
    circuit_breaker: string;
    available: boolean;
  };
  circuit_breaker: {
    state: string;
    available: boolean;
  };
  document_processor: {
    available: boolean;
    backend: string;
  };
  trend_detection: {
    available: boolean;
  };
  cached_trends: {
    has_data: boolean;
    count: number;
  };
}

// API calls
export const intelligenceApi = {
  /**
   * Chat with Rashid using the Pydantic AI agent.
   */
  chatWithRashid: async (
    message: string,
    language: string = "en",
    sessionId: string = ""
  ): Promise<RashidResponse> => {
    return apiRequest<RashidResponse>("/intelligence/rashid/chat/", {
      method: "POST",
      body: { message, language, session_id: sessionId },
    });
  },

  /**
   * Get emerging skills (trending up in job postings).
   */
  getEmergingSkills: async (days: number = 30): Promise<EmergingSkill[]> => {
    const data = await apiRequest<{ emerging_skills: EmergingSkill[] }>(
      "/intelligence/trends/emerging/",
      { params: { days } }
    );
    return data.emerging_skills;
  },

  /**
   * Get declining skills (trending down in job postings).
   */
  getDecliningSkills: async (days: number = 30): Promise<DecliningSkill[]> => {
    const data = await apiRequest<{ declining_skills: DecliningSkill[] }>(
      "/intelligence/trends/declining/",
      { params: { days } }
    );
    return data.declining_skills;
  },

  /**
   * Start an async research job.
   */
  startResearch: async (
    query: string,
    type: string = "market"
  ): Promise<ResearchTask> => {
    return apiRequest<ResearchTask>("/intelligence/research/", {
      method: "POST",
      body: { query, type },
    });
  },

  /**
   * Verify an email address.
   */
  verifyEmail: async (email: string): Promise<EmailVerificationResult> => {
    return apiRequest<EmailVerificationResult>("/intelligence/verify-email/", {
      method: "POST",
      body: { email },
    });
  },

  /**
   * List all available platform tools.
   */
  listTools: async (): Promise<PlatformTool[]> => {
    const data = await apiRequest<{ tools: PlatformTool[] }>("/intelligence/tools/");
    return data.tools;
  },

  /**
   * Admin: Get intelligence service health.
   */
  getHealth: async (): Promise<IntelligenceHealth> => {
    return apiRequest<IntelligenceHealth>("/intelligence/health/");
  },

  /**
   * Admin: Get trends dashboard data.
   */
  getTrendsDashboard: async () => {
    return apiRequest<any>("/intelligence/admin/trends/");
  },

  // --- Knowledge Graph ---

  /**
   * Get skill neighborhood graph.
   */
  getSkillGraph: async (skillName: string, depth: number = 2) => {
    return apiRequest<any>(
      `/intelligence/graph/skill/${encodeURIComponent(skillName)}/`,
      { params: { depth } }
    );
  },

  /**
   * Get skills required for a role.
   */
  getRoleSkillsGraph: async (roleTitle: string) => {
    return apiRequest<any>(
      `/intelligence/graph/role/${encodeURIComponent(roleTitle)}/skills/`
    );
  },

  /**
   * Get career paths from a role.
   */
  getCareerPathGraph: async (roleTitle: string) => {
    return apiRequest<any>(
      `/intelligence/graph/role/${encodeURIComponent(roleTitle)}/paths/`
    );
  },

  /**
   * Get skill gaps for a target role.
   */
  getSkillGaps: async (role: string) => {
    return apiRequest<any>("/intelligence/graph/skill-gaps/", {
      params: { role },
    });
  },

  // --- Content Pipeline ---

  /**
   * Admin: Generate content piece.
   */
  generateContent: async (
    type: string,
    role: string,
    options: { language?: string; company?: string; days?: number } = {}
  ) => {
    return apiRequest<any>("/intelligence/content/generate/", {
      method: "POST",
      body: { type, role, ...options },
    });
  },

  // --- Marketing Intelligence ---

  /**
   * Admin: Platform metrics.
   */
  getPlatformMetrics: async () => {
    return apiRequest<any>("/intelligence/admin/metrics/");
  },

  /**
   * Admin: Market gaps analysis.
   */
  getMarketGaps: async () => {
    return apiRequest<any>("/intelligence/admin/market-gaps/");
  },

  /**
   * Admin: Content opportunities.
   */
  getContentOpportunities: async () => {
    return apiRequest<any>("/intelligence/admin/content-opportunities/");
  },
};
