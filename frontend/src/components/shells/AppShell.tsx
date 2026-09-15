import { Layout } from "@/components/Layout";

/**
 * Shared authenticated shell. `AuthNavbar` is already role-aware (candidate vs
 * employer), so all in-app pages should render inside this shell instead of
 * bypassing it with a bespoke full-page wrapper. This is what keeps navigation,
 * footer, page transitions, and the `#main-content` landmark consistent.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  return <Layout>{children}</Layout>;
}
