"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { User, LoginInput, RegisterInput } from "@/types";
import { api, ApiError } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (input: LoginInput) => Promise<User>;
  register: (input: RegisterInput) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async (): Promise<User | null> => {
    try {
      const currentUser = await api.getMe();
      setUser(currentUser);
      return currentUser;
    } catch {
      setUser(null);
      return null;
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      setLoading(true);
      await refreshUser();
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (input: LoginInput): Promise<User> => {
    const res = await api.login(input);
    setUser(res.user);
    return res.user;
  };

  const register = async (input: RegisterInput): Promise<User> => {
    const res = await api.register(input);
    setUser(res.user);
    return res.user;
  };

  const logout = async (): Promise<void> => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
