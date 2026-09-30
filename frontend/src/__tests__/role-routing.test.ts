import { describe, it, expect } from "vitest";
import { roleHome, postAuthDestination } from "@/lib/role-routing";

/**
 * Guards the Company-vs-Individual routing contract (acceptance scenarios).
 * A regression here is the "company account lands on the individual dashboard"
 * bug, so these assertions are the deterministic safety net for the routing
 * resolver that Login + RequireRole both rely on.
 */
describe("roleHome — role → default home", () => {
  it("routes an employer (company) to the employer dashboard", () => {
    expect(roleHome("employer")).toBe("/app/employer/dashboard");
  });

  it("routes an admin to the admin console", () => {
    expect(roleHome("admin")).toBe("/admin");
  });

  it("routes a jobseeker (individual) to the candidate dashboard", () => {
    expect(roleHome("jobseeker")).toBe("/app/dashboard");
  });

  it("routes a legacy 'user' role to the candidate dashboard", () => {
    expect(roleHome("user")).toBe("/app/dashboard");
  });

  it("does NOT send an employer to the individual dashboard", () => {
    expect(roleHome("employer")).not.toBe("/app/dashboard");
  });

  it("falls back to the individual dashboard only for undefined/null role", () => {
    expect(roleHome(undefined)).toBe("/app/dashboard");
    expect(roleHome(null)).toBe("/app/dashboard");
  });
});

describe("postAuthDestination — where to go after auth", () => {
  it("sends an employer to the employer dashboard when there is no deep-link", () => {
    expect(postAuthDestination("employer")).toBe("/app/employer/dashboard");
  });

  it("sends an individual to the candidate dashboard", () => {
    expect(postAuthDestination("jobseeker")).toBe("/app/dashboard");
  });

  it("honors a gated deep-link (from) over the role home", () => {
    expect(postAuthDestination("employer", "/app/employer/jobs/new")).toBe(
      "/app/employer/jobs/new",
    );
  });

  it("ignores a generic-dashboard 'from' and uses the role home instead", () => {
    // A stale from=/app/dashboard must not override an employer's real home.
    expect(postAuthDestination("employer", "/app/dashboard")).toBe(
      "/app/employer/dashboard",
    );
  });
});
