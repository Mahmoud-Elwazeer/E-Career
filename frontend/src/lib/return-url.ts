/**
 * Safe post-login "return URL" handling.
 *
 * Two independent sources can request where a user should land after
 * authenticating:
 *  1. React Router navigation state (`location.state.from`) — set when an
 *     in-app guard (RequireAuth/RequireRole) redirects to /login.
 *  2. A `?next=` query parameter — set when an EXTERNAL caller (e.g. the
 *     USAM Master Ecosystem site) deep-links straight to /login with an
 *     intended destination, since it cannot set React Router state across
 *     a plain <a href> navigation.
 *
 * Both are untrusted input and must be validated before use: a value like
 * `https://evil.example.com` or `//evil.example.com` must never be honored,
 * or this becomes an open-redirect vector (login page redirects anywhere
 * an attacker wants after a legitimate auth).
 *
 * Rule: only an internal path starting with a single `/` (not `//`, not
 * `/\`, no scheme) is accepted. Anything else falls back to `null`, and
 * callers should use the role-based default destination instead.
 */

/** Returns `to` if it's a safe internal path, otherwise `null`. */
export function sanitizeReturnTo(to: string | null | undefined): string | null {
  if (!to) return null;
  // Reject anything that isn't a same-origin relative path. In particular:
  //  - "https://x.com/..." / "http://x.com/..." (absolute URL)
  //  - "//x.com/..." (protocol-relative — browsers treat this as external)
  //  - "/\x.com" or any backslash trick some browsers normalize to "//"
  //  - any value containing a colon before the first slash (custom schemes)
  if (!to.startsWith("/")) return null;
  if (to.startsWith("//")) return null;
  if (to.startsWith("/\\")) return null;
  // A relative path must not smuggle a scheme like "/\t/evil.com" or similar;
  // disallow control characters and whitespace outright.
  if (/[\s\u0000-\u001f]/.test(to)) return null;
  return to;
}

/** Reads `?next=` from a location-like search string and validates it. */
export function readNextParam(search: string): string | null {
  try {
    const params = new URLSearchParams(search);
    return sanitizeReturnTo(params.get("next"));
  } catch {
    return null;
  }
}
