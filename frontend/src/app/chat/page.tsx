/**
 * Chat page
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { CitationPanel } from '@/components/chat/CitationPanel';
import { Loading } from '@/components/ui/Loading';
import { useEffect, useRef, useState } from 'react';

const EXAMPLE_QUESTIONS = [
  'რა არის დღგ-ს განაკვეთი საქართველოში?',
  'ვინ არის საშემოსავლო გადასახადის გადამხდელი?',
  'რა არის მიკრო ბიზნესის სტატუსი?',
  'როგორ ხდება დღგ-ს დაბრუნება?',
  'რა არის საწარმოს მოგების გადასახადი?',
];

export default function ChatPage() {
  const searchParams = useSearchParams();
  const conversationId = searchParams.get('id') || undefined;

  const { messages, isLoading, error, sendMessage } = useChat({
    conversationId,
    mode: 'tax',
    language: 'ka',
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [openCitationIndex, setOpenCitationIndex] = useState<number | null>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleExampleClick = (question: string) => {
    sendMessage(question);
  };

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
            <h3 className="text-xl font-semibold text-text mb-2">გამარჯობა!</h3>
            <p className="text-text-light max-w-md mb-6">
              დაუსვით კითხვა საქართველოს საგადასახადო კოდექსთან დაკავშირებით
            </p>

            {/* Example Questions */}
            <div className="max-w-2xl w-full space-y-2">
              <p className="text-sm text-text-light mb-3">სწრაფი კითხვები:</p>
              <div className="grid gap-2">
                {EXAMPLE_QUESTIONS.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleExampleClick(question)}
                    className="text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary-50 transition-colors text-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index}>
            <MessageBubble message={message} isUser={message.role === 'user'} />

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
              <p className="text-sm">შეცდომა: {error.message}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
