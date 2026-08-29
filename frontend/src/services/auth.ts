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
  role: "user" | "admin" | "employer";
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
  last_name: string
): Promise<AuthResponse> {
  const data = await apiRequest<AuthResponse>("/auth/register/", {
    method: "POST",
    body: { email, password, password_confirm, first_name, last_name },
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
