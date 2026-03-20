import { apiRequest } from "./client";
import type { Job } from "./jobs";

// ── Saved Jobs ────────────────────────────────────────────────────────────────

export interface SavedJob {
  id: number;
  job: Job;
  saved_at: string;
}

export async function fetchSavedJobs(): Promise<SavedJob[]> {
  const data = await apiRequest<any>("/users/me/saved-jobs/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function saveJob(job_id: number): Promise<SavedJob> {
  return apiRequest<SavedJob>("/users/me/saved-jobs/", {
    method: "POST",
    body: { job_id },
  });
}

export async function unsaveJob(savedJobId: number): Promise<void> {
  return apiRequest<void>(`/users/me/saved-jobs/${savedJobId}/`, {
    method: "DELETE",
  });
}

// ── Alerts ────────────────────────────────────────────────────────────────────

export interface Alert {
  id: number;
  uuid: string;
  keyword: string;
  work_mode: string;
  industry: string;
  frequency: "instant" | "daily" | "weekly";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function fetchAlerts(): Promise<Alert[]> {
  const data = await apiRequest<any>("/users/me/alerts/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function createAlert(payload: {
  keyword?: string;
  work_mode?: string;
  industry?: string;
  frequency?: "instant" | "daily" | "weekly";
}): Promise<Alert> {
  return apiRequest<Alert>("/users/me/alerts/", {
    method: "POST",
    body: payload,
  });
}

export async function updateAlert(
  uuid: string,
  updates: Partial<Pick<Alert, "frequency" | "is_active">>
): Promise<Alert> {
  return apiRequest<Alert>(`/users/me/alerts/${uuid}/`, {
    method: "PATCH",
    body: updates,
  });
}

export async function deleteAlert(uuid: string): Promise<void> {
  return apiRequest<void>(`/users/me/alerts/${uuid}/`, { method: "DELETE" });
}

// ── Notifications ─────────────────────────────────────────────────────────────

export interface Notification {
  id: number;
  uuid: string;
  title: string;
  body: string | null;
  type: string | null;
  is_read: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export async function fetchNotifications(): Promise<Notification[]> {
  const data = await apiRequest<any>("/users/me/notifications/");
  if (Array.isArray(data)) return data;
  if (data?.results) return data.results;
  return data;
}

export async function markNotificationRead(uuid: string): Promise<Notification> {
  return apiRequest<Notification>(`/users/me/notifications/${uuid}/`, {
    method: "PATCH",
  });
}

export async function markAllNotificationsRead(): Promise<{ marked_read: number }> {
  return apiRequest<{ marked_read: number }>("/users/me/notifications/mark-all-read/", {
    method: "POST",
  });
}
