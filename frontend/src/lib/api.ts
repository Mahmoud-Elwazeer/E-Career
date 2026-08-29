/**
 * Unified API client - Main entry point for all HTTP requests
 *
 * Replaces both services/api.ts (axios) and services/client.ts (fetch)
 * with a single, consistent interface.
 *
 * Usage:
 *   import api from "@/lib/api";
 *   const response = await api.get("/api/v1/endpoint");
 *   const data = await api.post("/api/v1/endpoint", { body });
 */

// NOTE: services/api.ts (axios-based client) was deleted in commit 35f797b
// ("Migrated frontend services to apiRequest") — services/client.ts's
// fetch-based apiRequest() is now the single canonical HTTP client. Re-export
// it here so any remaining `import api from "@/lib/api"; api.get(...)` call
// sites can be migrated incrementally without a default export dead-ending
// on a deleted module.
export { apiRequest } from "@/services/client";

// Job-specific exports for backwards compatibility
export {
  fetchJobs,
  fetchJobBySlug,
  fetchJobBySlug as fetchJobById,
  fetchSimilarJobs,
  fetchCompanies,
  fetchSources,
  logApplyClick,
} from "@/services/jobs";

export type { Job, Company, Source, Tag } from "@/services/jobs";

// Compatibility stubs for logging
export async function logJobView(_jobId: string) {}
export async function logSearch(_query: string, _filters: Record<string, string>, _count: number) {}

export function getCachedCompany(_id: string) { return undefined; }
export function getCachedSource(_id: string) { return undefined; }
