/**
 * Core HTTP client (fetch-based) — handles base URL, JWT auth headers,
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

/**
 * Perform a fetch with automatic JWT attach + single-flight 401 refresh/retry.
 * Shared by both the JSON `apiRequest` and the binary `apiRequestBlob` helpers
 * so every network call gets the same auth behavior.
 */
async function fetchWithAuth(
  path: string,
  options: RequestOptions
): Promise<Response> {
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

  const token = auth ? getAccessToken() : null;
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

  return res;
}

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const res = await fetchWithAuth(path, options);

  // No-content responses (e.g. 204 from DELETE) have no body to parse. Some
  // endpoints send 204 with a JSON Content-Type but an empty body, which makes
  // res.json() throw — guard for that so deletes don't spuriously "fail".
  if (res.status === 204 || res.headers.get("Content-Length") === "0") {
    return undefined as T;
  }

  // Parse response
  const contentType = res.headers.get("Content-Type") ?? "";
  const isJson = contentType.includes("application/json");
  let data: unknown;
  if (isJson) {
    // Body may still be empty on some 200/201 responses; tolerate that.
    const raw = await res.text();
    data = raw ? JSON.parse(raw) : null;
  } else {
    data = await res.text();
  }

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

export interface BlobResponse {
  blob: Blob;
  filename: string | null;
  contentType: string;
}

/**
 * Request a binary/file response (PDF, DOCX, etc.) with the same auth + refresh
 * behavior as `apiRequest`. Returns the raw Blob plus a filename parsed from the
 * Content-Disposition header, so callers can trigger a real browser download.
 * Using `apiRequest` for binary endpoints corrupts the bytes (it decodes them as
 * text), so any file-download endpoint must use this instead.
 */
export async function apiRequestBlob(
  path: string,
  options: RequestOptions = {}
): Promise<BlobResponse> {
  const res = await fetchWithAuth(path, options);

  if (!res.ok) {
    // Error bodies are JSON even for a binary endpoint — surface the message.
    let message = `Request failed with status ${res.status}`;
    let data: unknown = null;
    try {
      data = await res.json();
      message = (data as any)?.message || (data as any)?.detail || message;
    } catch {
      /* non-JSON error body; keep default message */
    }
    throw new ApiError(message, res.status, data);
  }

  const contentType = res.headers.get("Content-Type") ?? "application/octet-stream";
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const filename = parseFilename(disposition);
  const blob = await res.blob();
  return { blob, filename, contentType };
}

/** Extract a filename from a Content-Disposition header, if present. */
function parseFilename(disposition: string): string | null {
  // Prefer RFC 5987 filename*=UTF-8''... then fall back to filename="..."
  const utf8Match = /filename\*=(?:UTF-8'')?["']?([^"';]+)/i.exec(disposition);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }
  const plainMatch = /filename=["']?([^"';]+)/i.exec(disposition);
  return plainMatch?.[1] ?? null;
}

/** Trigger a browser download for a fetched Blob. */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Give the browser a tick to start the download before revoking.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
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
