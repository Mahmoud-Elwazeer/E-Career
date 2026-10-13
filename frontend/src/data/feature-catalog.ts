/**
 * Canonical feature catalog — the SINGLE source of truth for every major
 * platform feature's identity, routing, and discovery metadata.
 *
 * Why this exists: before this file, the same feature list was hand-copied
 * with slightly different wording into 4 separate places (PublicNavMenu,
 * audience-content, FeatureShowcase, ForYou) with no shared identity between
 * them. That made it impossible to answer "does every feature have a stable
 * link" without re-auditing by hand each time, and is exactly the kind of
 * drift this file prevents going forward.
 *
 * The actual data lives in `feature-catalog.json` (plain JSON, no TS runtime
 * required) so it can be read by BOTH this app (via a normal import) and
 * `scripts/generate-usam-master-catalogue.mjs` (plain Node, no ts-node) to
 * produce `USAM-MASTER-FEATURE-LINKS.md` + `.json` for the USAM Master
 * Ecosystem integration — an entry in that JSON file IS the integration
 * contract. Keep `to` pointing at a route that really exists in `App.tsx`.
 *
 * Access levels:
 *  - "public": works for anyone, no auth.
 *  - "auth": requires sign-in as any role (RequireAuth).
 *  - "employer": requires the employer/admin role (RequireEmployer).
 *  - "admin": requires the admin role (RequireAdmin).
 *
 * Status:
 *  - "live": the route renders a real, wired page/feature today.
 *  - "beta": live but still rough/evolving (none currently — flag honestly
 *    if introduced rather than defaulting everything to "live").
 *  - "planned": referenced by the product narrative but not yet routed.
 *  - "unavailable": temporarily disabled/removed.
 */
import rawFeatures from "./feature-catalog.json";

export type FeatureAccess = "public" | "auth" | "employer" | "admin";
export type FeatureStatus = "live" | "beta" | "planned" | "unavailable";
export type FeatureAudience = "individual" | "employer" | "admin" | "everyone";
export type FeatureCategory =
  | "discover" // search/browse/matching
  | "career-tools" // resume, cover letters, talent score, career graph
  | "ai-coaching" // Rasheed, interview prep, assessments
  | "insights" // salary, skills, companies
  | "account" // profile, settings, notifications, billing
  | "hiring" // employer: post jobs, search talent, pools, team, analytics
  | "platform"; // admin / API docs

export interface FeatureEntry {
  /** Stable identifier — never reuse or repurpose once published externally. */
  id: string;
  nameEn: string;
  nameAr: string;
  shortDescEn: string;
  shortDescAr: string;
  audience: FeatureAudience;
  category: FeatureCategory;
  icon: string; // lucide-react icon component name, resolved by consumers
  /** Direct application / deep-link route within this app. */
  to: string;
  /**
   * Public overview URL for this feature, if a dedicated explainer page
   * exists. Most individual tools don't have one of their own — they are
   * explained on /features and the audience pages instead. Company-facing
   * capabilities are introduced via /for-businesses.
   */
  overviewTo?: string;
  access: FeatureAccess;
  status: FeatureStatus;
  /** Other catalog entry ids this feature is commonly paired with. */
  related?: string[];
  /** Short, honest limitation note (shown nowhere by default, but kept for
   *  the integration catalogue / internal audits). Omit when there is none. */
  note?: string;
}

export const FEATURES: FeatureEntry[] = rawFeatures as FeatureEntry[];

export function getFeature(id: string): FeatureEntry | undefined {
  return FEATURES.find((f) => f.id === id);
}

export function featuresByAudience(audience: FeatureAudience): FeatureEntry[] {
  return FEATURES.filter((f) => f.audience === audience || f.audience === "everyone");
}

export function featuresByCategory(category: FeatureCategory): FeatureEntry[] {
  return FEATURES.filter((f) => f.category === category);
}
