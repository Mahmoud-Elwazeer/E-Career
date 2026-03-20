/**
 * Core Axios client — handles base URL, JWT auth headers,
 * and automatic token refresh on 401.
 */

const API_BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000") + "/api/v1";

const TOKEN_KEY = "usam_access";
const REFRESH_KEY = "usam_refresh";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ── Fetch wrapper ────────────────────────────────────────────────────────────

type Method = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

interface RequestOptions {
  method?: Method;
  body?: unknown;
  formData?: FormData;
  auth?: boolean; // default true
  params?: Record<string, string | number | boolean | undefined>;
}

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  if (!params) return url;
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
  return qs ? `${url}?${qs}` : url;
}

async function doRefresh(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) {
      clearTokens();
      return null;
    }
    const data = await res.json();
    const newAccess = data?.data?.access ?? data?.access;
    const newRefresh = data?.data?.refresh ?? data?.refresh;
    if (newAccess) {
      setTokens(newAccess, newRefresh ?? refresh);
      return newAccess;
    }
    clearTokens();
    return null;
  } catch {
    clearTokens();
    return null;
  }
}

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, formData, auth = true, params } = options;

  const makeRequest = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (body && !formData) headers["Content-Type"] = "application/json";

    return fetch(buildUrl(path, params), {
      method,
      headers,
      body: formData ?? (body ? JSON.stringify(body) : undefined),
    });
  };

  let token = auth ? getAccessToken() : null;
  let res = await makeRequest(token);

  // Auto-refresh on 401
  if (res.status === 401 && auth && getRefreshToken()) {
    if (isRefreshing) {
      // Wait for existing refresh
      const freshToken = await new Promise<string | null>((resolve) => {
        refreshQueue.push(resolve);
      });
      res = await makeRequest(freshToken);
    } else {
      isRefreshing = true;
      const freshToken = await doRefresh();
      isRefreshing = false;
      refreshQueue.forEach((cb) => cb(freshToken));
      refreshQueue = [];
      if (freshToken) {
        res = await makeRequest(freshToken);
      } else {
        // Refresh failed — dispatch a custom event so AuthProvider can handle it
        window.dispatchEvent(new CustomEvent("auth:logout"));
      }
    }
  }

  // Parse response
  const contentType = res.headers.get("Content-Type") ?? "";
  const isJson = contentType.includes("application/json");
  const data = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    const message =
      (data as any)?.message ||
      (data as any)?.detail ||
      `Request failed with status ${res.status}`;
    throw new ApiError(message, res.status, data);
  }

  // Unwrap envelope
  if (isJson && typeof data === "object" && data !== null && "data" in data) {
    return (data as any).data as T;
  }
  return data as T;
}

export class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}
