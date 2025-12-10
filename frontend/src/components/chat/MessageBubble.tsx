/**
 * MessageBubble component
 */

'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn, formatDate } from '@/lib/utils';
import type { Message } from '@/lib/types';

export interface MessageBubbleProps {
  message: Message;
  isUser: boolean;
}

/**
 * Highlight article citations in text and make them clickable
 */
const highlightCitations = (text: string): string => {
  // Pattern to match Georgian article citations
  const citationPattern = /მუხლი\s+(\d+(?:\.\d+)?(?:\.[ა-ჰ])?)/g;

  return text.replace(citationPattern, (match, articleNum) => {
    const url = `https://matsne.gov.ge/ka/document/view/1043717#ARTICLE_${articleNum}`;
    return `[**${match}**](${url})`;
  });
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser }) => {
  const [showTimestamp, setShowTimestamp] = useState(false);

  // Process content to highlight citations for assistant messages
  const processedContent = !isUser ? highlightCitations(message.content) : message.content;

  // Get mode badge info
  const getModeInfo = (mode?: string) => {
    switch (mode) {
      case 'tax':
        return { label: 'საგადასახადო კოდექსი', color: 'bg-blue-100 text-blue-800', bgTint: 'bg-blue-50' };
      case 'dispute':
        return { label: 'დავები', color: 'bg-purple-100 text-purple-800', bgTint: 'bg-purple-50' };
      case 'document':
        return { label: 'დოკუმენტი', color: 'bg-green-100 text-green-800', bgTint: 'bg-green-50' };
      case 'auto':
        return { label: 'ავტომატური', color: 'bg-gray-100 text-gray-800', bgTint: 'bg-gray-50' };
      default:
        return null;
    }
  };

  const modeInfo = !isUser && message.mode_used ? getModeInfo(message.mode_used) : null;

  return (
    <div
      className={cn(
        'flex w-full mb-4 group',
        isUser ? 'justify-end' : 'justify-start'
      )}
      onMouseEnter={() => setShowTimestamp(true)}
      onMouseLeave={() => setShowTimestamp(false)}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3 relative',
          isUser
            ? 'bg-primary text-white'
            : cn(
                'border border-gray-200 text-text',
                modeInfo?.bgTint || 'bg-white'
              )
        )}
      >
        {/* Mode badge for assistant messages */}
        {!isUser && modeInfo && (
          <div className="mb-2 flex items-center gap-2">
            <span className={cn(
              'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
              modeInfo.color
            )}>
              {modeInfo.label}
            </span>
          </div>
        )}

        {/* Timestamp on hover */}
        {showTimestamp && (
          <div
            className={cn(
              'absolute -top-6 text-xs text-text-light',
              isUser ? 'right-0' : 'left-0'
            )}
          >
            {formatDate(message.timestamp)}
          </div>
        )}

        {/* Message content */}
        {!isUser ? (
          <div
            className={cn(
              'prose prose-sm max-w-none',
              'prose-p:my-2 prose-ul:my-2 prose-ol:my-2',
              'prose-a:text-primary prose-a:font-semibold prose-a:no-underline hover:prose-a:underline',
              'prose-strong:text-accent prose-strong:font-bold'
            )}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {processedContent}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="whitespace-pre-wrap break-words">{message.content}</div>
        )}

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
