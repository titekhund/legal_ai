/**
 * Sidebar component
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { useConversations } from '@/hooks/useConversations';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/ui/Loading';
import { formatTimeAgo, truncate } from '@/lib/utils';
import { cn } from '@/lib/utils';

export interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentConversationId?: string;
  onNewConversation?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  currentConversationId,
  onNewConversation,
}) => {
  const { conversations, isLoading, deleteConversation } = useConversations({
    autoLoad: true,
  });

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (confirm('ნამდვილად გსურთ ამ საუბრის წაშლა?')) {
      await deleteConversation(id);
    }
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 h-full bg-white border-r border-gray-200 z-50 transition-transform duration-300 ease-in-out',
          'w-80 lg:w-64',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-text">საუბრები</h2>
              <button
                onClick={onToggle}
                className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            {onNewConversation && (
              <Button onClick={onNewConversation} className="w-full" size="sm">
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

          {/* Conversations list */}
          <div className="flex-1 overflow-y-auto p-2">
            {isLoading ? (
              <Loading size="sm" />
            ) : conversations.length === 0 ? (
              <div className="text-center text-text-light text-sm py-8">
                საუბრები ჯერ არ არის
              </div>
            ) : (
              <div className="space-y-1">
                {conversations.map((conversation) => (
                  <Link
                    key={conversation.conversation_id}
                    href={`/chat?id=${conversation.conversation_id}`}
                    className={cn(
                      'block p-3 rounded-lg hover:bg-gray-100 transition-colors group',
                      currentConversationId === conversation.conversation_id &&
                        'bg-primary-50 hover:bg-primary-100'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text truncate">
                          {truncate(conversation.last_message_preview, 50)}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-text-light">
                            {conversation.message_count} შეტყობინება
                          </span>
                          <span className="text-xs text-text-lighter">•</span>
                          <span className="text-xs text-text-light">
                            {formatTimeAgo(conversation.updated_at)}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => handleDelete(conversation.conversation_id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-opacity"
                      >
                        <svg
                          className="w-4 h-4 text-red-500"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
