/**
 * Re-exports from services layer for backward compatibility.
 * All components should migrate to importing from @/services/jobs directly.
 */
export type { Job, Company, Source, Tag } from "@/services/jobs";

export type LocationType = "remote" | "onsite" | "hybrid";
export type ExperienceLevel = "entry" | "mid" | "senior" | "lead";
export type Industry =
  | "technology" | "finance" | "healthcare" | "education"
  | "marketing" | "engineering" | "design" | "sales";

export interface SavedJob {
  jobId: string;
  savedAt: string;
}

export interface Alert {
  id: string;
  keyword: string;
  locationType?: LocationType;
  industry?: Industry;
  createdAt: string;
}
