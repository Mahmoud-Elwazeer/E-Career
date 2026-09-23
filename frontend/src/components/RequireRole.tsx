import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import type { AppUser } from "@/services/auth";
import { roleHome } from "@/lib/role-routing";

type Role = AppUser["role"];

interface RequireRoleProps {
  children: React.ReactNode;
  allowed: Role[];
}

export function RequireRole({ children, allowed }: RequireRoleProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return null;

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (!user || !allowed.includes(user.role)) {
    // Send a wrong-role user to their OWN home rather than a generic list.
    return <Navigate to={roleHome(user?.role)} replace />;
  }

  return <>{children}</>;
}

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  return <RequireRole allowed={["admin"]}>{children}</RequireRole>;
}

export function RequireEmployer({ children }: { children: React.ReactNode }) {
  return <RequireRole allowed={["employer", "admin"]}>{children}</RequireRole>;
}
