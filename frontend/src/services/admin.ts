import { apiRequest } from "./client";
import type { Job } from "./jobs";

// ── Stats ─────────────────────────────────────────────────────────────────────

export interface AdminStats {
  total_jobs: number;
  pending_review: number;
  active_sources: number;
  total_saves: number;
  total_clicks: number;
  total_views: number;
  total_users: number;
  jobs_this_week: number;
}

export interface AdminCharts {
  jobs_by_industry: { name: string; count: number }[];
  jobs_by_source: { name: string; count: number }[];
  recent_activity?: any[];
}

export async function fetchAdminStats(): Promise<AdminStats> {
  return apiRequest<AdminStats>("/analytics/stats/");
}

export async function fetchAdminCharts(): Promise<AdminCharts> {
  return apiRequest<AdminCharts>("/analytics/charts/");
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function fetchClickAnalytics(days = 30) {
  return apiRequest<any>("/analytics/clicks/", { params: { days } });
}

export async function fetchSearchAnalytics(days = 30) {
  return apiRequest<any>("/analytics/searches/", { params: { days } });
}

export async function fetchConversionAnalytics(days = 30) {
  return apiRequest<any>("/analytics/conversion/", { params: { days } });
}

export async function fetchActivityLogs(page = 1, action?: string) {
  return apiRequest<any>("/analytics/activity-logs/", {
    params: { page, ...(action ? { action } : {}) },
  });
}

// ── Jobs (admin CRUD) ─────────────────────────────────────────────────────────

export async function adminCreateJob(data: Record<string, unknown>) {
  return apiRequest<Job>("/jobs/", { method: "POST", body: data });
}

export async function adminUpdateJob(slug: string, data: Record<string, unknown>) {
  return apiRequest<Job>(`/jobs/${slug}/`, { method: "PATCH", body: data });
}

export async function adminDeleteJob(slug: string) {
  return apiRequest<void>(`/jobs/${slug}/`, { method: "DELETE" });
}

export async function adminPublishJob(slug: string) {
  return apiRequest<Job>(`/jobs/${slug}/`, { method: "PATCH", body: { status: "active" } });
}

export async function adminArchiveJob(slug: string) {
  return apiRequest<Job>(`/jobs/${slug}/`, { method: "PATCH", body: { status: "archived" } });
}

// ── Companies (admin CRUD) ────────────────────────────────────────────────────

export async function adminFetchAllCompanies() {
  const data = await apiRequest<any>("/jobs/companies/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function adminCreateCompany(data: {
  name: string;
  industry?: string;
  website?: string;
  about?: string;
  logo_url?: string;
  snippet?: string;
}) {
  return apiRequest<any>("/jobs/companies/", { method: "POST", body: data });
}

export async function adminUpdateCompany(slug: string, data: Record<string, unknown>) {
  return apiRequest<any>(`/jobs/companies/${slug}/`, { method: "PATCH", body: data });
}

export async function adminDeleteCompany(slug: string) {
  return apiRequest<void>(`/jobs/companies/${slug}/`, { method: "DELETE" });
}

// ── Sources (admin CRUD) ──────────────────────────────────────────────────────

export async function adminFetchAllSources() {
  const data = await apiRequest<any>("/jobs/sources/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function adminCreateSource(data: {
  name: string;
  url?: string;
  type?: string;
  logo_url?: string;
}) {
  return apiRequest<any>("/jobs/sources/", { method: "POST", body: data });
}

export async function adminUpdateSource(slug: string, data: Record<string, unknown>) {
  return apiRequest<any>(`/jobs/sources/${slug}/`, { method: "PATCH", body: data });
}

export async function adminDeleteSource(slug: string) {
  return apiRequest<void>(`/jobs/sources/${slug}/`, { method: "DELETE" });
}

// ── Tags ──────────────────────────────────────────────────────────────────────

export async function adminFetchAllTags() {
  const data = await apiRequest<any>("/jobs/tags/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function adminCreateTag(name: string, category?: string) {
  return apiRequest<any>("/jobs/tags/", { method: "POST", body: { name, category } });
}

export async function adminDeleteTag(slug: string) {
  return apiRequest<void>(`/jobs/tags/${slug}/`, { method: "DELETE" });
}

// ── Feature Flags ─────────────────────────────────────────────────────────────

export async function fetchFeatureFlags() {
  const data = await apiRequest<any>("/admin-api/feature-flags/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function updateFeatureFlag(uuid: string, updates: { is_enabled: boolean }) {
  return apiRequest<any>(`/admin-api/feature-flags/${uuid}/`, {
    method: "PATCH",
    body: updates,
  });
}

// ── Media ─────────────────────────────────────────────────────────────────────

export async function adminFetchMedia() {
  const data = await apiRequest<any>("/admin-api/media/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function adminUploadMedia(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequest<any>("/admin-api/media/", { method: "POST", formData: fd });
}

export async function adminDeleteMedia(uuid: string) {
  return apiRequest<void>(`/admin-api/media/${uuid}/`, { method: "DELETE" });
}

// ── CSV Import ───────────────────────────────────────────────────────────────
export async function adminCsvImport(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<{ imported: number; skipped: number; total: number; errors: string[] }>(
    "/admin-api/csv-import/",
    { method: "POST", formData },
  );
}
