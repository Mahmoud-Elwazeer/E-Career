import { apiRequest } from "./client";

/** ESCO/O*NET-style skill from the taxonomy (apps/skills). */
export interface Skill {
  id: string;
  name: string;
  name_ar?: string;
  type?: string;
  category?: string;
  level?: number;
  description?: string;
  children_count?: number;
}

export interface Occupation {
  id: string;
  name: string;
  name_ar?: string;
  description?: string;
  skills_count?: number;
}

function unwrapList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object" && Array.isArray((data as any).results)) {
    return (data as any).results as T[];
  }
  return [];
}

export const skillsApi = {
  /** Browse the skill taxonomy (paginated on the backend). */
  list: async (): Promise<Skill[]> => {
    const data = await apiRequest<unknown>("/skills/skills/", { auth: false });
    return unwrapList<Skill>(data);
  },
  /** Full-text search of skills. */
  search: async (q: string): Promise<Skill[]> => {
    const data = await apiRequest<unknown>("/skills/skills/search/", { params: { q }, auth: false });
    return unwrapList<Skill>(data);
  },
  /** Related skills for a given skill id. */
  related: async (id: string): Promise<Skill[]> => {
    const data = await apiRequest<unknown>(`/skills/skills/${id}/related/`, { auth: false });
    return unwrapList<Skill>(data);
  },
  /** Browse occupations. */
  occupations: async (): Promise<Occupation[]> => {
    const data = await apiRequest<unknown>("/skills/occupations/", { auth: false });
    return unwrapList<Occupation>(data);
  },
};

export default skillsApi;
