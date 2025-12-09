/**
 * Chat layout with sidebar
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import APIClient from '@/lib/api';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentConversationId = searchParams.get('id') || undefined;
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  const handleNewChat = () => {
    router.push('/chat');
    setSidebarOpen(false);
  };

  // Check API status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        await APIClient.health();
        setIsOnline(true);
      } catch (error) {
        setIsOnline(false);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-screen">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and title */}
            <div className="flex items-center gap-3">
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
              <span className="text-xl font-semibold text-text">
                {process.env.NEXT_PUBLIC_APP_NAME || 'TaxCode AI'}
              </span>
            </div>

            {/* Status and Actions */}
            <div className="flex items-center gap-4">
              {/* API Status Indicator */}
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isOnline === null
                      ? 'bg-gray-400'
                      : isOnline
                      ? 'bg-green-500'
                      : 'bg-red-500'
                  }`}
                />
                <span className="text-sm text-text-light hidden sm:inline">
                  {isOnline === null ? 'შემოწმება...' : isOnline ? 'დაკავშირებული' : 'გათიშული'}
                </span>
              </div>

              {/* New Chat Button */}
              <button
                onClick={handleNewChat}
                className="inline-flex items-center px-3 py-2 border border-primary text-primary rounded-lg hover:bg-primary-50 transition-colors text-sm font-medium"
              >
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
                <span className="hidden sm:inline">ახალი საუბარი</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          currentConversationId={currentConversationId}
          onNewConversation={handleNewChat}
        />

        {/* Main content */}
        <main className="flex-1 lg:ml-64">
          {children}
        </main>

        {/* Mobile sidebar toggle button */}
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed bottom-4 right-4 lg:hidden bg-primary text-white p-3 rounded-full shadow-lg z-30"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
