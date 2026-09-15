import type { ReactNode } from "react";

/**
 * Route-level enter/exit motion is now owned by <RouteTransition> at the App
 * router boundary (RTL-aware, reduced-motion safe). This component used to add a
 * second mount-fade inside Layout/AppShell, which double-animated every page.
 * It is kept as a passthrough so existing Layout/AppShell usages stay valid.
 */
export function PageTransition({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
