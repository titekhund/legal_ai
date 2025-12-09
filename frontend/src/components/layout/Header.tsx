/**
 * Header component
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

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
          </div>
        </div>
      </div>
    </header>
  );
};
