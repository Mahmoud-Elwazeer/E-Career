import { describe, it, expect } from "vitest";
import { sanitizeReturnTo, readNextParam } from "@/lib/return-url";

/**
 * Open-redirect protection for the login "return to" mechanism. This is the
 * safety net for the USAM Master Ecosystem integration: external callers can
 * deep-link through /login?next=..., so every value from that source MUST be
 * validated before it is ever used as a navigation target.
 */
describe("sanitizeReturnTo", () => {
  it("accepts a plain internal path", () => {
    expect(sanitizeReturnTo("/app/jobs")).toBe("/app/jobs");
  });

  it("accepts an internal path with a query string", () => {
    expect(sanitizeReturnTo("/app/jobs?q=python&location=cairo")).toBe(
      "/app/jobs?q=python&location=cairo",
    );
  });

  it("rejects an absolute external URL (https)", () => {
    expect(sanitizeReturnTo("https://evil.example.com")).toBeNull();
  });

  it("rejects an absolute external URL (http)", () => {
    expect(sanitizeReturnTo("http://evil.example.com/app/jobs")).toBeNull();
  });

  it("rejects a protocol-relative URL", () => {
    expect(sanitizeReturnTo("//evil.example.com")).toBeNull();
  });

  it("rejects a backslash-trick path", () => {
    expect(sanitizeReturnTo("/\\evil.example.com")).toBeNull();
  });

  it("rejects a value with an embedded scheme", () => {
    expect(sanitizeReturnTo("javascript:alert(1)")).toBeNull();
  });

  it("rejects a value not starting with a slash", () => {
    expect(sanitizeReturnTo("app/jobs")).toBeNull();
  });

  it("rejects null, undefined, and empty string", () => {
    expect(sanitizeReturnTo(null)).toBeNull();
    expect(sanitizeReturnTo(undefined)).toBeNull();
    expect(sanitizeReturnTo("")).toBeNull();
  });

  it("rejects a value containing control characters", () => {
    expect(sanitizeReturnTo("/app/jobs\n/evil")).toBeNull();
    expect(sanitizeReturnTo("/app/jobs\t/evil")).toBeNull();
  });
});

describe("readNextParam", () => {
  it("extracts and validates a safe ?next= value", () => {
    expect(readNextParam("?next=%2Fapp%2Fjobs")).toBe("/app/jobs");
  });

  it("returns null when ?next= is an external URL", () => {
    expect(readNextParam("?next=https%3A%2F%2Fevil.example.com")).toBeNull();
  });

  it("returns null when there is no next param", () => {
    expect(readNextParam("?other=value")).toBeNull();
  });

  it("returns null for an empty search string", () => {
    expect(readNextParam("")).toBeNull();
  });
});
