/**
 * MessageBubble component
 */

'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { Message } from '@/lib/types';

export interface MessageBubbleProps {
  message: Message;
  isUser: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser }) => {
  return (
    <div
      className={cn(
        'flex w-full mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3',
          isUser
            ? 'bg-primary text-white'
            : 'bg-white border border-gray-200 text-text'
        )}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>

        {/* Show sources indicator for assistant messages */}
        {!isUser && message.sources && message.sources.tax_articles.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="flex items-center text-xs text-text-light">
              <svg
                className="w-4 h-4 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span>
                {message.sources.tax_articles.length} მუხლი მოიძებნა
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
