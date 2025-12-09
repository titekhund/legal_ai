/**
 * ChatWindow component
 */

'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { CitationPanel } from './CitationPanel';
import { Loading } from '@/components/ui/Loading';
import type { ChatSources } from '@/lib/types';

export interface ChatWindowProps {
  conversationId?: string;
  mode?: 'tax' | 'dispute' | 'document';
  language?: 'ka' | 'en';
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  conversationId,
  mode = 'tax',
  language = 'ka',
}) => {
  const { messages, isLoading, error, sendMessage } = useChat({
    conversationId,
    mode,
    language,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [openCitationIndex, setOpenCitationIndex] = useState<number | null>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <svg
              className="w-16 h-16 text-text-lighter mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <h3 className="text-xl font-semibold text-text mb-2">
              {language === 'ka' ? 'გამარჯობა!' : 'Hello!'}
            </h3>
            <p className="text-text-light max-w-md">
              {language === 'ka'
                ? 'დაუსვით კითხვა საქართველოს საგადასახადო კოდექსთან დაკავშირებით'
                : 'Ask a question about the Georgian Tax Code'}
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index}>
            <MessageBubble
              message={message}
              isUser={message.role === 'user'}
            />

            {/* Show citations for assistant messages */}
            {message.role === 'assistant' && (
              <div className="mb-4">
                <CitationPanel
                  sources={message.sources || null}
                  isOpen={openCitationIndex === index}
                  onToggle={() =>
                    setOpenCitationIndex(openCitationIndex === index ? null : index)
                  }
                />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
              <Loading size="sm" />
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3">
              <p className="text-sm">
                {language === 'ka' ? 'შეცდომა:' : 'Error:'} {error.message}
              </p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
      />
    </div>
  );
};
