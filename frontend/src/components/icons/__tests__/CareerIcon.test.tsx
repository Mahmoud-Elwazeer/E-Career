/**
 * CareerIcon Tests
 *
 * - Known names resolve to the registered lucide icon (no fallback)
 * - Unknown names fall back gracefully instead of throwing/rendering nothing
 * - Decorative usage (no `label`) is aria-hidden
 * - Standalone usage (`label` passed) exposes an accessible name via role="img"
 * - `active` toggles the stateful bookmark/notification variants
 * - `spinning` applies the spin class but respects prefers-reduced-motion via CSS utility
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { CareerIcon, isKnownCareerIcon } from "../CareerIcon";

describe("CareerIcon", () => {
  it("renders a known icon without throwing", () => {
    const { container } = render(<CareerIcon name="job" className="h-4 w-4" />);
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("falls back to a placeholder icon for unknown names instead of rendering nothing", () => {
    const { container } = render(<CareerIcon name="totally-not-a-real-icon" />);
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
  });

  it("reports known vs unknown names via isKnownCareerIcon", () => {
    expect(isKnownCareerIcon("job")).toBe(true);
    expect(isKnownCareerIcon("bookmark")).toBe(true);
    expect(isKnownCareerIcon("not-a-real-name")).toBe(false);
  });

  it("is aria-hidden by default (decorative, paired with visible text)", () => {
    const { container } = render(<CareerIcon name="job" />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg).not.toHaveAttribute("role");
  });

  it("exposes an accessible name when `label` is provided for standalone usage", () => {
    const { container } = render(<CareerIcon name="notification" label="3 unread notifications" />);
    const svg = container.querySelector("svg");
    expect(svg).not.toHaveAttribute("aria-hidden");
    expect(svg).toHaveAttribute("role", "img");
    expect(svg).toHaveAttribute("aria-label", "3 unread notifications");
  });

  it("switches to the filled bookmark variant when active=true", () => {
    const unsaved = render(<CareerIcon name="bookmark" />);
    const saved = render(<CareerIcon name="bookmark" active />);
    // Different lucide icons render different path data; just assert they differ.
    expect(unsaved.container.innerHTML).not.toEqual(saved.container.innerHTML);
  });

  it("applies the spin class with a motion-reduce override when spinning=true", () => {
    const { container } = render(<CareerIcon name="refresh" spinning className="h-4 w-4" />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("class")).toContain("animate-spin");
    expect(svg?.getAttribute("class")).toContain("motion-reduce:animate-none");
  });

  it("does not spin when spinning is false/omitted", () => {
    const { container } = render(<CareerIcon name="refresh" className="h-4 w-4" />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("class")).not.toContain("animate-spin");
  });
});
