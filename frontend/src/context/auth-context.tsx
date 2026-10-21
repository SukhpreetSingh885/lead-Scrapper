"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  organization_id: string;
  is_superuser: boolean;
}

interface AuthContextType {
  user: CurrentUser | null;
  isLoading: boolean;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  logout: async () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const headers: Record<string, string> = { Accept: "application/json" };
      if (typeof window !== "undefined") {
        const token = localStorage.getItem("indialeads_token");
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
      }

      const res = await fetch("/api/v1/auth/me", {
        headers,
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        setUser(null);
        if (res.status === 401 && typeof window !== "undefined") {
          localStorage.removeItem("indialeads_token");
          if (!window.location.pathname.startsWith("/login")) {
            window.location.href = `/login?redirect=${encodeURIComponent(
              window.location.pathname + window.location.search
            )}`;
          }
        }
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const logout = async () => {
    try {
      const headers: Record<string, string> = {};
      if (typeof window !== "undefined") {
        const token = localStorage.getItem("indialeads_token");
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
      }
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers,
        credentials: "include",
      });
    } catch (e) {
      console.error("Logout request failed:", e);
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem("indialeads_token");
        window.location.href = "/login";
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, logout, refreshUser: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

