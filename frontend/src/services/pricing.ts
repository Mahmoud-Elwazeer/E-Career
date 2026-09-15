/**
 * Pricing / plans service — reads the public, read-only plans endpoint.
 */
import { apiRequest } from "./client";

export interface Plan {
  uuid: string;
  name: string;
  description: string;
  job_posting_limit: number;
  candidate_search_limit: number;
  ai_features_enabled: boolean;
  feature_flags: Record<string, unknown>;
}

interface PlansResponse {
  plans: Plan[];
}

export async function getPublicPlans(): Promise<Plan[]> {
  // apiRequest unwraps the {success, data} envelope → returns {plans:[...]}.
  const res = await apiRequest<PlansResponse>("/core/plans/", { auth: false });
  return res?.plans ?? [];
}
