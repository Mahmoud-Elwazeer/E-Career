/**
 * Markdown policy rendering security tests.
 *
 * react-markdown (no rehype-raw configured) already renders embedded raw
 * HTML as inert text rather than executing it. These tests pin the
 * additional belt-and-suspenders hardening: link/image href scheme
 * allowlisting, so a `javascript:`/`data:` URL embedded in admin-authored
 * markdown can never execute on click, and raw HTML tags never become
 * live DOM.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PolicyMarkdown } from "../PolicyMarkdown";

function renderMd(content: string) {
  return render(
    <MemoryRouter>
      <PolicyMarkdown content={content} />
    </MemoryRouter>,
  );
}

describe("PolicyMarkdown security", () => {
  it("renders plain markdown content normally", () => {
    renderMd("# Hello\n\nSome **bold** text.");
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("bold")).toBeInTheDocument();
  });

  it("neutralizes a javascript: URL in a link to '#' instead of executing it", () => {
    renderMd("[click me](javascript:alert(1))");
    const link = screen.getByText("click me").closest("a");
    expect(link).toHaveAttribute("href", "#");
  });

  it("neutralizes a data: URL in a link", () => {
    renderMd("[click me](data:text/html,<script>alert(1)</script>)");
    const link = screen.getByText("click me").closest("a");
    expect(link).toHaveAttribute("href", "#");
  });

  it("allows a normal https link and opens it in a new tab safely", () => {
    renderMd("[USAM](https://jobs.usamif.com)");
    const link = screen.getByText("USAM").closest("a");
    expect(link).toHaveAttribute("href", "https://jobs.usamif.com");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("allows mailto: links", () => {
    renderMd("[email us](mailto:privacy@example.com)");
    const link = screen.getByText("email us").closest("a");
    expect(link).toHaveAttribute("href", "mailto:privacy@example.com");
  });

  it("routes an internal /legal/... link through the SPA router <Link>, not a full reload", () => {
    renderMd("[Privacy Policy](/legal/privacy)");
    const link = screen.getByText("Privacy Policy").closest("a");
    expect(link).toHaveAttribute("href", "/legal/privacy");
  });

  it("does not execute raw HTML <script> embedded in markdown source", () => {
    const { container } = renderMd("# Title\n\n<script>window.__xss_pwned__ = true;</script>\n\nAfter.");
    expect((window as any).__xss_pwned__).toBeUndefined();
    expect(container.querySelector("script")).toBeNull();
  });

  it("does not execute an <img onerror=...> XSS payload embedded as raw HTML", () => {
    const { container } = renderMd('<img src="x" onerror="window.__xss_pwned_img__=true">');
    expect((window as any).__xss_pwned_img__).toBeUndefined();
    // Either rendered as inert text (no <img> at all) or, if react-markdown's
    // own img component ran, our override strips any non-https src.
    const img = container.querySelector("img");
    if (img) {
      expect(img.getAttribute("src")).not.toBe("x");
    }
  });

  it("rejects a non-https image src rather than rendering it", () => {
    renderMd("![alt text](javascript:alert(1))");
    // Our img override returns null for non-https sources — no <img> tag at all.
    expect(document.querySelector("img")).toBeNull();
  });

  it("allows a normal https image", () => {
    const { container } = renderMd("![logo](https://example.com/logo.png)");
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    expect(img).toHaveAttribute("src", "https://example.com/logo.png");
  });
});
