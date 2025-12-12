/**
 * Header component with auth status and usage display
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

export interface HeaderProps {
  title?: string;
  showNewChatButton?: boolean;
  onNewChat?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title = process.env.NEXT_PUBLIC_APP_NAME || 'TaxCode AI',
  showNewChatButton = false,
  onNewChat,
}) => {
  const router = useRouter();
  const { user, usageInfo, isAuthenticated, isLoading, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
    router.push('/');
  };

  // Calculate usage percentage for progress bar
  const dailyUsagePercent = usageInfo
    ? Math.min(100, (usageInfo.daily_used / usageInfo.daily_limit) * 100)
    : 0;

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and title */}
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                />
              </svg>
            </div>
            <span className="text-xl font-semibold text-text">{title}</span>
          </Link>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {showNewChatButton && onNewChat && (
              <Button onClick={onNewChat} variant="outline" size="sm">
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                ახალი საუბარი
              </Button>
            )}

            {/* Auth section */}
            {!isLoading && (
              <>
                {isAuthenticated && user ? (
                  <div className="flex items-center gap-3">
                    {/* Usage indicator */}
                    {usageInfo && (
                      <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-gray-50 rounded-lg">
                        <div className="text-xs text-gray-600">
                          <span className="font-medium">{usageInfo.daily_remaining}</span>
                          <span className="text-gray-400">/{usageInfo.daily_limit}</span>
                          <span className="ml-1">დღეს</span>
                        </div>
                        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-300 ${
                              dailyUsagePercent > 80
                                ? 'bg-red-500'
                                : dailyUsagePercent > 50
                                ? 'bg-yellow-500'
                                : 'bg-green-500'
                            }`}
                            style={{ width: `${100 - dailyUsagePercent}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* User menu */}
                    <div className="relative">
                      <button
                        onClick={() => setShowUserMenu(!showUserMenu)}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-primary">
                            {user.email.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <svg
                          className={`w-4 h-4 text-gray-500 transition-transform ${
                            showUserMenu ? 'rotate-180' : ''
                          }`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </button>

                      {/* Dropdown menu */}
                      {showUserMenu && (
                        <>
                          <div
                            className="fixed inset-0 z-10"
                            onClick={() => setShowUserMenu(false)}
                          />
                          <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
                            <div className="px-4 py-3 border-b border-gray-100">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {user.full_name || user.email}
                              </p>
                              <p className="text-xs text-gray-500 truncate">
                                {user.email}
                              </p>
                            </div>

                            {/* Usage details */}
                            {usageInfo && (
                              <div className="px-4 py-3 border-b border-gray-100 space-y-2">
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-600">დღის ლიმიტი:</span>
                                  <span className="font-medium">
                                    {usageInfo.daily_used}/{usageInfo.daily_limit}
                                  </span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full ${
                                      dailyUsagePercent > 80
                                        ? 'bg-red-500'
                                        : dailyUsagePercent > 50
                                        ? 'bg-yellow-500'
                                        : 'bg-green-500'
                                    }`}
                                    style={{ width: `${dailyUsagePercent}%` }}
                                  />
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className="text-gray-600">თვის ლიმიტი:</span>
                                  <span className="font-medium">
                                    {usageInfo.monthly_used}/{usageInfo.monthly_limit}
                                  </span>
                                </div>
                                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-blue-500"
                                    style={{
                                      width: `${Math.min(
                                        100,
                                        (usageInfo.monthly_used / usageInfo.monthly_limit) * 100
                                      )}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            )}

                            <div className="py-1">
                              <button
                                onClick={handleLogout}
                                className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 transition-colors"
                              >
                                გასვლა
                              </button>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Link href="/auth/login">
                      <Button variant="outline" size="sm">
                        შესვლა
                      </Button>
                    </Link>
                    <Link href="/auth/register">
                      <Button size="sm">
                        რეგისტრაცია
                      </Button>
                    </Link>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
