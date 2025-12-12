'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading, usageInfo, refreshUsage } = useAuth();

  // Refresh usage on mount
  useEffect(() => {
    if (isAuthenticated) {
      refreshUsage();
    }
  }, [isAuthenticated, refreshUsage]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">იტვირთება...</p>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return null; // Will redirect
  }

  // Check if daily limit is reached
  if (usageInfo && usageInfo.daily_remaining <= 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
            <svg
              className="w-8 h-8 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-2xl font-bold text-gray-900">
            დღის ლიმიტი ამოიწურა
          </h2>
          <p className="mt-3 text-gray-600">
            თქვენ გამოიყენეთ დღეში დაშვებული {usageInfo.daily_limit} მოთხოვნა.
            ლიმიტი განახლდება ხვალ.
          </p>
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">დღის მოთხოვნები:</span>
              <span className="font-medium text-red-600">
                {usageInfo.daily_used}/{usageInfo.daily_limit}
              </span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-red-500 w-full" />
            </div>
          </div>
          <div className="mt-6 space-y-3">
            <Link href="/" className="block">
              <Button variant="outline" className="w-full">
                მთავარ გვერდზე დაბრუნება
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Check if monthly limit is reached
  if (usageInfo && usageInfo.monthly_remaining <= 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto">
            <svg
              className="w-8 h-8 text-orange-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-2xl font-bold text-gray-900">
            თვის ლიმიტი ამოიწურა
          </h2>
          <p className="mt-3 text-gray-600">
            თქვენ გამოიყენეთ თვეში დაშვებული {usageInfo.monthly_limit} მოთხოვნა.
            ლიმიტი განახლდება შემდეგ თვეს.
          </p>
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">თვის მოთხოვნები:</span>
              <span className="font-medium text-orange-600">
                {usageInfo.monthly_used}/{usageInfo.monthly_limit}
              </span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-orange-500 w-full" />
            </div>
          </div>
          <div className="mt-6 space-y-3">
            <Link href="/" className="block">
              <Button variant="outline" className="w-full">
                მთავარ გვერდზე დაბრუნება
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
