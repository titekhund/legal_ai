'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { APIClient, getStoredUser, getStoredToken, clearAuthData } from '@/lib/api';
import type { User, UsageInfo, RegisterRequest, LoginRequest } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  usageInfo: UsageInfo | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  refreshUsage: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [usageInfo, setUsageInfo] = useState<UsageInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Refresh user data from API
  const refreshUser = useCallback(async () => {
    try {
      const userData = await APIClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If token is invalid, clear auth data
      clearAuthData();
      setUser(null);
      setUsageInfo(null);
    }
  }, []);

  // Refresh usage data from API
  const refreshUsage = useCallback(async () => {
    if (!user) return;
    try {
      const usage = await APIClient.getUsageInfo();
      setUsageInfo(usage);
    } catch (error) {
      console.error('Failed to refresh usage:', error);
    }
  }, [user]);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const token = getStoredToken();
      const storedUser = getStoredUser();

      if (token && storedUser) {
        setUser(storedUser);
        // Verify token is still valid by fetching fresh user data
        try {
          const freshUser = await APIClient.getCurrentUser();
          setUser(freshUser);
          const usage = await APIClient.getUsageInfo();
          setUsageInfo(usage);
        } catch {
          // Token is invalid, clear auth
          clearAuthData();
          setUser(null);
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  // Login handler
  const login = useCallback(async (data: LoginRequest) => {
    const response = await APIClient.login(data);
    setUser(response.user);
    // Fetch usage info after login
    try {
      const usage = await APIClient.getUsageInfo();
      setUsageInfo(usage);
    } catch (error) {
      console.error('Failed to fetch usage after login:', error);
    }
  }, []);

  // Register handler
  const register = useCallback(async (data: RegisterRequest) => {
    const response = await APIClient.register(data);
    setUser(response.user);
    // Fetch usage info after registration
    try {
      const usage = await APIClient.getUsageInfo();
      setUsageInfo(usage);
    } catch (error) {
      console.error('Failed to fetch usage after registration:', error);
    }
  }, []);

  // Logout handler
  const logout = useCallback(() => {
    APIClient.logout();
    setUser(null);
    setUsageInfo(null);
  }, []);

  const value: AuthContextType = {
    user,
    usageInfo,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
    refreshUsage,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
