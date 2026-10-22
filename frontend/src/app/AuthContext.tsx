import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from '../lib/apiClient';
import { User, UserRole, PermittedScope, UserProfile, LoginResponse } from '../types';

export interface AuthContextType {
  user: User | null;
  permissions: string[];
  scope: PermittedScope | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [scope, setScope] = useState<PermittedScope | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async () => {
    try {
      const data = await api.get<UserProfile>('/auth/me');
      setUser(data.user);
      setPermissions(data.permissions || []);
      setScope(data.permitted_scope || null);
    } catch {
      setUser(null);
      setPermissions([]);
      setScope(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      await api.post<LoginResponse>('/auth/login', { email, password });
      await refreshUser();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.warn('Logout request warning:', err);
    } finally {
      setUser(null);
      setPermissions([]);
      setScope(null);
    }
  };

  const hasPermission = (perm: string): boolean => {
    if (!user) return false;
    return permissions.includes(perm);
  };

  const hasRole = (roles: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    const allowed = Array.isArray(roles) ? roles : [roles];
    // Map system_admin and admin interchangeably
    if (allowed.includes('admin') || allowed.includes('system_admin')) {
      if (user.role === 'admin' || user.role === 'system_admin') return true;
    }
    return allowed.includes(user.role);
  };

  const value: AuthContextType = {
    user,
    permissions,
    scope,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
    hasPermission,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
