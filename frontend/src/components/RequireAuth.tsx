import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return null;

  if (!isAuthenticated) {
    // Preserve the query string too (e.g. /app/jobs?q=python) — a bookmarked
    // or shared deep link must still resolve to the same filtered view after
    // the user signs in, not just the bare route.
    const from = `${location.pathname}${location.search}`;
    return <Navigate to="/login" state={{ from }} replace />;
  }

  return <>{children}</>;
}
