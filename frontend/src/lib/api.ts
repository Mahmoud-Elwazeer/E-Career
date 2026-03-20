/**
 * Legacy api.ts shim — delegates to src/services/jobs.ts
 * Keeps existing page components working without changes.
 */
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

// Compatibility stubs kept for components that import these
export async function logJobView(_jobId: string) {}
export async function logSearch(_query: string, _filters: Record<string, string>, _count: number) {}

export function getCachedCompany(_id: string) { return undefined; }
export function getCachedSource(_id: string) { return undefined; }
