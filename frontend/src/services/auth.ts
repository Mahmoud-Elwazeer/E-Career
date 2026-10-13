import { apiRequest, setTokens, clearTokens } from "./client";

export interface AppUser {
  id: number;
  uuid: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  avatar: string | null;
  avatar_url: string | null;
  // Backend Role choices: jobseeker (default) | employer | admin | user (legacy).
  // "jobseeker"/"user" both mean the individual/candidate product.
  role: "jobseeker" | "user" | "admin" | "employer";
  status: string;
  created_at: string;
}

interface AuthResponse {
  user: AppUser;
  access: string;
  refresh: string;
}

export async function register(
  email: string,
  password: string,
  password_confirm: string,
  first_name: string,
  last_name: string,
  account_type: "individual" | "company" = "individual"
): Promise<AuthResponse> {
  const data = await apiRequest<AuthResponse>("/auth/register/", {
    method: "POST",
    body: { email, password, password_confirm, first_name, last_name, account_type },
    auth: false,
  });
  setTokens(data.access, data.refresh);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await apiRequest<AuthResponse>("/auth/login/", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
  setTokens(data.access, data.refresh);
  return data;
}

export async function logout(refresh: string) {
  try {
    await apiRequest("/auth/logout/", {
      method: "POST",
      body: { refresh },
    });
  } catch {
    // Always clear tokens even if request fails
  } finally {
    clearTokens();
  }
}

export async function resetPassword(email: string) {
  return apiRequest("/auth/password/reset/", {
    method: "POST",
    body: { email },
    auth: false,
  });
}

export async function resetPasswordConfirm(
  uid: string,
  token: string,
  new_password: string,
  new_password_confirm: string
) {
  return apiRequest("/auth/password/reset/confirm/", {
    method: "POST",
    body: { uid, token, new_password, new_password_confirm },
    auth: false,
  });
}

export async function getMe(): Promise<AppUser> {
  return apiRequest<AppUser>("/users/me/");
}

export async function updateMe(data: Partial<AppUser>): Promise<AppUser> {
  return apiRequest<AppUser>("/users/me/", { method: "PATCH", body: data });
}

export async function uploadAvatar(file: File): Promise<AppUser> {
  const fd = new FormData();
  fd.append("avatar", file);
  return apiRequest<AppUser>("/users/me/avatar/", { method: "POST", formData: fd });
}

export async function changePassword(
  current_password: string,
  new_password: string,
  new_password_confirm: string
) {
  return apiRequest("/users/me/change-password/", {
    method: "POST",
    body: { current_password, new_password, new_password_confirm },
  });
}

export async function deleteAccount() {
  return apiRequest("/users/me/", { method: "DELETE" });
}

// ── GDPR self-service (Privacy Center) ───────────────────────────────────────
// Scoped data export + grace-period account deletion, distinct from the
// immediate `deleteAccount()` above (which hard-deletes via /users/me/).
// These give a 30-day cancellable grace period and a downloadable export.

export interface DataExportRequestStatus {
  request_id: string;
  status: "pending" | "processing" | "completed" | "failed" | "expired";
  requested_at: string;
  completed_at?: string | null;
  expires_at?: string | null;
  download_url?: string;
  file_size?: number;
  error?: string;
}

export async function requestDataExport(): Promise<{ request_id: string; status?: string; estimated_time?: string }> {
  return apiRequest("/auth/data-export/", { method: "POST" });
}

export async function getDataExportStatus(requestId: string): Promise<DataExportRequestStatus> {
  return apiRequest(`/auth/data-export/${requestId}/`);
}

export async function listDataExports(): Promise<{ exports: DataExportRequestStatus[] }> {
  return apiRequest("/auth/data-exports/");
}

export interface DeletionStatus {
  pending: boolean;
  scheduled_for?: string;
  request_id?: string;
  days_remaining?: number;
}

export async function requestAccountDeletionGrace(reason?: string): Promise<{ request_id: string; scheduled_for: string; grace_period_days: number }> {
  return apiRequest("/auth/account/deletion-request/", { method: "DELETE", body: reason ? { reason } : undefined });
}

export async function cancelAccountDeletionGrace(): Promise<void> {
  await apiRequest("/auth/account/cancel-deletion/", { method: "POST" });
}

export async function getAccountDeletionStatus(): Promise<DeletionStatus> {
  return apiRequest("/auth/account/deletion-status/");
}
