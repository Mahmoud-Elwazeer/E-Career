import {
  createContext, useContext, useState, useCallback,
  useEffect, useRef, type ReactNode,
} from "react";
import {
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  resetPassword as apiResetPassword,
  getMe,
  type AppUser,
} from "@/services/auth";
import { getAccessToken, getRefreshToken, clearTokens } from "@/services/client";

interface AuthContextValue {
  user: AppUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, firstName: string, lastName: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: Error | null }>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const initialized = useRef(false);

  // ✅ NORMALIZE USER HERE
  const normalizeUser = (u: any): AppUser => {
    return {
      ...u,
      name:
        u.name ||
        `${u.first_name || ""} ${u.last_name || ""}`.trim() ||
        "User",
      avatar: u.avatar || "/default-avatar.png",
    };
  };

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    getMe()
      .then((u) => setUser(normalizeUser(u)))
      .catch(() => clearTokens())
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    const handler = () => {
      setUser(null);
      clearTokens();
    };
    window.addEventListener("auth:logout", handler);
    return () => window.removeEventListener("auth:logout", handler);
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password);
    setUser(normalizeUser(data.user)); // ✅ FIX
  }, []);

  const signUp = useCallback(async (email: string, password: string, firstName: string, lastName: string) => {
    const data = await apiRegister(email, password, password, firstName, lastName);
    setUser(normalizeUser(data.user)); // ✅ FIX
  }, []);

  const signInWithGoogle = useCallback(async () => {
    const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
    window.location.href = `${base}/accounts/google/login/`;
  }, []);

  const signOut = useCallback(async () => {
    const refresh = getRefreshToken() ?? "";
    await apiLogout(refresh);
    setUser(null);
  }, []);

  const resetPassword = useCallback(async (email: string) => {
    try {
      await apiResetPassword(email);
      return { error: null };
    } catch (e) {
      return { error: e instanceof Error ? e : new Error(String(e)) };
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const u = await getMe();
      setUser(normalizeUser(u)); // ✅ FIX
    } catch {
      setUser(null);
      clearTokens();
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        signIn,
        signUp,
        signInWithGoogle,
        signOut,
        resetPassword,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export type { AppUser };