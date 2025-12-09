/**
 * Chat layout with sidebar
 */

'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { Footer } from '@/components/layout/Footer';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentConversationId = searchParams.get('id') || undefined;
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNewChat = () => {
    router.push('/chat');
    setSidebarOpen(false);
  };

  return (
    <div className="flex flex-col h-screen">
      <Header showNewChatButton onNewChat={handleNewChat} />

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
