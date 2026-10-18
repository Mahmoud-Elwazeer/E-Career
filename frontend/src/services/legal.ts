import { apiRequest } from "@/services/client";

export interface PolicyVersion {
  uuid: string;
  document_slug: string;
  document_title: string;
  version_label: string;
  locale: string;
  jurisdiction: string;
  status: string;
  content_markdown: string;
  summary_of_changes: string;
  material_change: boolean;
  is_machine_translated: boolean;
  effective_at: string | null;
}

export interface PolicyDocument {
  uuid: string;
  slug: string;
  doc_type: string;
  title: string;
  is_active: boolean;
  live_version: PolicyVersion | null;
}

export interface ConsentPurpose {
  uuid: string;
  key: string;
  category: string;
  label: string;
  description: string;
  is_required: boolean;
  granted: boolean | null;
}

export interface CookieCategoryDef {
  uuid: string;
  key: "necessary" | "functional" | "analytics" | "marketing";
  label: string;
  description: string;
  is_essential: boolean;
  is_active: boolean;
}

export type CookieAction = "accept_all" | "reject_non_essential" | "custom";

export interface CookieConsentSnapshot {
  uuid: string;
  action: CookieAction;
  categories: Record<string, boolean>;
  created_at: string;
}

export interface PrivacyRequest {
  uuid: string;
  request_type: string;
  status: string;
  jurisdiction: string;
  details: string;
  resolution_note: string;
  due_at: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  events: { uuid: string; event_type: string; note: string; created_at: string }[];
}

export interface LegalEntityPublic {
  legal_entity_name: string;
  registered_address: string;
  tax_or_registration_id: string;
  dpo_name: string;
  dpo_email: string;
  privacy_contact_email: string;
  support_contact_email: string;
  default_refund_window_days: number | null;
  is_configured: boolean;
  updated_at: string;
}

export interface AIProcessingDisclosure {
  uuid: string;
  feature_key: string;
  feature_label: string;
  description: string;
  data_categories_used: string;
  makes_final_decision: boolean;
  retention_note: string;
  is_active: boolean;
}

export interface MarketingPreference {
  email_marketing_opt_in: boolean;
  sms_marketing_opt_in: boolean;
  unsubscribed_at: string | null;
  updated_at: string;
}

// ── Policies ─────────────────────────────────────────────────────────────────

export async function listPolicies(): Promise<PolicyDocument[]> {
  return apiRequest<PolicyDocument[]>("/legal/policies/");
}

export async function getPolicy(slug: string, locale = "en"): Promise<PolicyVersion> {
  return apiRequest<PolicyVersion>(`/legal/policies/${slug}/`, { params: { locale }, auth: false });
}

export async function acceptPolicy(slug: string, method = "settings"): Promise<void> {
  await apiRequest(`/legal/policies/${slug}/accept/`, { method: "POST", body: { method } });
}

// ── Consent purposes ──────────────────────────────────────────────────────────

export async function listConsentPurposes(): Promise<ConsentPurpose[]> {
  return apiRequest<ConsentPurpose[]>("/legal/consent-purposes/", { auth: false });
}

export async function setConsent(purpose: string, granted: boolean, method = "settings"): Promise<void> {
  await apiRequest("/legal/consent/", { method: "POST", body: { purpose, granted, method } });
}

// ── Marketing preference ──────────────────────────────────────────────────────

export async function getMarketingPreference(): Promise<MarketingPreference> {
  return apiRequest<MarketingPreference>("/legal/marketing-preference/");
}

export async function updateMarketingPreference(
  patch: Partial<Pick<MarketingPreference, "email_marketing_opt_in" | "sms_marketing_opt_in">>,
): Promise<MarketingPreference> {
  return apiRequest<MarketingPreference>("/legal/marketing-preference/", { method: "PATCH", body: patch });
}

// ── Cookie consent ───────────────────────────────────────────────────────────

export async function listCookieCategories(): Promise<CookieCategoryDef[]> {
  return apiRequest<CookieCategoryDef[]>("/legal/cookie-categories/", { auth: false });
}

export async function recordCookieConsent(
  action: CookieAction,
  categories: Record<string, boolean>,
): Promise<CookieConsentSnapshot> {
  return apiRequest<CookieConsentSnapshot>("/legal/cookie-consent/", {
    method: "POST",
    body: { action, categories },
    auth: false,
  });
}

export async function getMyCookieConsent(): Promise<CookieConsentSnapshot | null> {
  return apiRequest<CookieConsentSnapshot | null>("/legal/cookie-consent/me/", { auth: false });
}

// ── Privacy Center / DSR ──────────────────────────────────────────────────────

export async function listPrivacyRequests(): Promise<PrivacyRequest[]> {
  const res = await apiRequest<{ results?: PrivacyRequest[] } | PrivacyRequest[]>("/legal/privacy-requests/");
  if (Array.isArray(res)) return res;
  return res?.results ?? [];
}

export async function openPrivacyRequest(
  request_type: string,
  details = "",
  jurisdiction = "OTHER",
): Promise<PrivacyRequest> {
  return apiRequest<PrivacyRequest>("/legal/privacy-requests/", {
    method: "POST",
    body: { request_type, details, jurisdiction },
  });
}

// ── Public legal-entity + AI disclosure registers ────────────────────────────

export async function getLegalEntityPublic(): Promise<LegalEntityPublic> {
  return apiRequest<LegalEntityPublic>("/legal/entity/", { auth: false });
}

export async function listAIDisclosures(): Promise<AIProcessingDisclosure[]> {
  return apiRequest<AIProcessingDisclosure[]>("/legal/ai-disclosures/", { auth: false });
}

export interface ProcessorPublic {
  uuid: string;
  name: string;
  purpose: string;
  data_categories: string;
  country: string;
  dpa_signed: boolean | null;
}

export interface DataTransferPublic {
  uuid: string;
  processor_name: string;
  destination_country: string;
  data_categories: string;
  mechanism: string;
}

export async function listProcessorsPublic(): Promise<ProcessorPublic[]> {
  return apiRequest<ProcessorPublic[]>("/legal/processors/", { auth: false });
}

export async function listDataTransfersPublic(): Promise<DataTransferPublic[]> {
  return apiRequest<DataTransferPublic[]>("/legal/transfers/", { auth: false });
}

// ── Admin Legal Control Plane ────────────────────────────────────────────────

export interface RetentionPolicyRow {
  uuid: string;
  data_category: string;
  description: string;
  retention_period_days: number | null;
  legal_basis: string;
  requires_legal_review: boolean;
  jurisdiction: string;
  reviewed_at: string | null;
}

export interface JurisdictionProfile {
  uuid: string;
  jurisdiction: string;
  regulator_name: string;
  law_name: string;
  dsr_sla_days: number | null;
  breach_notification_hours: number | null;
  minor_age_threshold: number | null;
  requires_legal_review: boolean;
  source_notes: string;
  updated_at: string;
}

function unwrapList<T>(res: { results?: T[] } | T[]): T[] {
  if (Array.isArray(res)) return res;
  return res?.results ?? [];
}

export async function adminListPolicyVersions(documentSlug?: string): Promise<PolicyVersion[]> {
  const res = await apiRequest<{ results?: PolicyVersion[] } | PolicyVersion[]>(
    "/legal/admin/versions/", { params: documentSlug ? { document: documentSlug } : undefined },
  );
  return unwrapList(res);
}

export async function adminTransitionPolicyVersion(uuid: string, newStatus: string): Promise<PolicyVersion> {
  return apiRequest(`/legal/admin/versions/${uuid}/transition/`, { method: "POST", body: { status: newStatus } });
}

export async function adminListRetention(): Promise<RetentionPolicyRow[]> {
  const res = await apiRequest<{ results?: RetentionPolicyRow[] } | RetentionPolicyRow[]>("/legal/admin/retention/");
  return unwrapList(res);
}

export async function adminUpdateRetention(uuid: string, patch: Partial<RetentionPolicyRow>): Promise<RetentionPolicyRow> {
  return apiRequest(`/legal/admin/retention/${uuid}/`, { method: "PATCH", body: patch });
}

export async function adminListJurisdictions(): Promise<JurisdictionProfile[]> {
  const res = await apiRequest<{ results?: JurisdictionProfile[] } | JurisdictionProfile[]>("/legal/admin/jurisdictions/");
  return unwrapList(res);
}

export async function adminListCookieCategories(): Promise<CookieCategoryDef[]> {
  const res = await apiRequest<{ results?: CookieCategoryDef[] } | CookieCategoryDef[]>("/legal/admin/cookie-categories/");
  return unwrapList(res);
}

export interface ProcessorRecordRow {
  uuid: string;
  name: string;
  purpose: string;
  data_categories: string;
  country: string;
  contract_reference: string;
  dpa_signed: boolean | null;
  is_active: boolean;
  notes: string;
  updated_at: string;
}

export async function adminListProcessors(): Promise<ProcessorRecordRow[]> {
  const res = await apiRequest<{ results?: ProcessorRecordRow[] } | ProcessorRecordRow[]>("/legal/admin/processors/");
  return unwrapList(res);
}

export async function adminListDsrQueue(statusFilter?: string): Promise<PrivacyRequest[]> {
  const res = await apiRequest<{ results?: PrivacyRequest[] } | PrivacyRequest[]>(
    "/legal/admin/privacy-requests/", { params: statusFilter ? { status: statusFilter } : undefined },
  );
  return unwrapList(res);
}

export async function adminTransitionDsr(uuid: string, status: string, note = ""): Promise<PrivacyRequest> {
  return apiRequest(`/legal/admin/privacy-requests/${uuid}/transition/`, { method: "POST", body: { status, note } });
}

export async function adminGetLegalEntity(): Promise<LegalEntityPublic> {
  return apiRequest<LegalEntityPublic>("/legal/admin/entity/");
}

export async function adminUpdateLegalEntity(patch: Partial<LegalEntityPublic>): Promise<LegalEntityPublic> {
  return apiRequest<LegalEntityPublic>("/legal/admin/entity/", { method: "PATCH", body: patch });
}
