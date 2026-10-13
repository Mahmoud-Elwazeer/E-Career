import type { AppUser } from "@/services/auth";
import { sanitizeReturnTo } from "@/lib/return-url";

/**
 * Single source of truth for "where does this role belong by default".
 *
 * The platform has three real roles on `AppUser.role`: "user" (individual /
 * professional), "employer" (company), and "admin". Historically every role
 * was redirected to the individual dashboard after login — an employer landing
 * on the candidate dashboard was the core "wrong dashboard" bug. This helper
 * fixes that in one place so Login, guards, and any future redirect agree.
 */
export type AppRole = AppUser["role"];

export function roleHome(role: AppRole | undefined | null): string {
  switch (role) {
    case "employer":
      return "/app/employer/dashboard";
    case "admin":
      return "/admin";
    default:
      return "/app/dashboard";
  }
}

/**
 * Resolve the post-auth destination. A deep-link the user was gated from
 * (`state.from`, or an external `?next=` param) wins, so long as it isn't
 * the generic dashboard default — otherwise we honor the role's real home.
 *
 * `from` is untrusted (it may originate from a `?next=` query param set by
 * an external caller like the USAM Master Ecosystem site) and is always
 * re-validated here via `sanitizeReturnTo`, even if a caller already
 * validated it once — this function must never return an attacker-supplied
 * external URL.
 */
export function postAuthDestination(role: AppRole | undefined | null, from?: string | null): string {
  const safeFrom = sanitizeReturnTo(from);
  if (safeFrom && safeFrom !== "/app/dashboard") return safeFrom;
  return roleHome(role);
}
