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
import { apiClient } from "./client";

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
    const { data } = await apiClient.post("/intelligence/rashid/chat/", {
      message,
      language,
      session_id: sessionId,
    });
    return data;
  },

  /**
   * Get emerging skills (trending up in job postings).
   */
  getEmergingSkills: async (days: number = 30): Promise<EmergingSkill[]> => {
    const { data } = await apiClient.get("/intelligence/trends/emerging/", {
      params: { days },
    });
    return data.emerging_skills;
  },

  /**
   * Get declining skills (trending down in job postings).
   */
  getDecliningSkills: async (days: number = 30): Promise<DecliningSkill[]> => {
    const { data } = await apiClient.get("/intelligence/trends/declining/", {
      params: { days },
    });
    return data.declining_skills;
  },

  /**
   * Start an async research job.
   */
  startResearch: async (
    query: string,
    type: string = "market"
  ): Promise<ResearchTask> => {
    const { data } = await apiClient.post("/intelligence/research/", {
      query,
      type,
    });
    return data;
  },

  /**
   * Verify an email address.
   */
  verifyEmail: async (email: string): Promise<EmailVerificationResult> => {
    const { data } = await apiClient.post("/intelligence/verify-email/", {
      email,
    });
    return data;
  },

  /**
   * List all available platform tools.
   */
  listTools: async (): Promise<PlatformTool[]> => {
    const { data } = await apiClient.get("/intelligence/tools/");
    return data.tools;
  },

  /**
   * Admin: Get intelligence service health.
   */
  getHealth: async (): Promise<IntelligenceHealth> => {
    const { data } = await apiClient.get("/intelligence/health/");
    return data;
  },

  /**
   * Admin: Get trends dashboard data.
   */
  getTrendsDashboard: async () => {
    const { data } = await apiClient.get("/intelligence/admin/trends/");
    return data;
  },

  // --- Knowledge Graph ---

  /**
   * Get skill neighborhood graph.
   */
  getSkillGraph: async (skillName: string, depth: number = 2) => {
    const { data } = await apiClient.get(
      `/intelligence/graph/skill/${encodeURIComponent(skillName)}/`,
      { params: { depth } }
    );
    return data;
  },

  /**
   * Get skills required for a role.
   */
  getRoleSkillsGraph: async (roleTitle: string) => {
    const { data } = await apiClient.get(
      `/intelligence/graph/role/${encodeURIComponent(roleTitle)}/skills/`
    );
    return data;
  },

  /**
   * Get career paths from a role.
   */
  getCareerPathGraph: async (roleTitle: string) => {
    const { data } = await apiClient.get(
      `/intelligence/graph/role/${encodeURIComponent(roleTitle)}/paths/`
    );
    return data;
  },

  /**
   * Get skill gaps for a target role.
   */
  getSkillGaps: async (role: string) => {
    const { data } = await apiClient.get("/intelligence/graph/skill-gaps/", {
      params: { role },
    });
    return data;
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
    const { data } = await apiClient.post("/intelligence/content/generate/", {
      type,
      role,
      ...options,
    });
    return data;
  },

  // --- Marketing Intelligence ---

  /**
   * Admin: Platform metrics.
   */
  getPlatformMetrics: async () => {
    const { data } = await apiClient.get("/intelligence/admin/metrics/");
    return data;
  },

  /**
   * Admin: Market gaps analysis.
   */
  getMarketGaps: async () => {
    const { data } = await apiClient.get("/intelligence/admin/market-gaps/");
    return data;
  },

  /**
   * Admin: Content opportunities.
   */
  getContentOpportunities: async () => {
    const { data } = await apiClient.get("/intelligence/admin/content-opportunities/");
    return data;
  },
};
