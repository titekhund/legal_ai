/**
 * useChat hook for managing chat state
 */

'use client';

import { useState, useCallback } from 'react';
import APIClient, { APIClientError } from '@/lib/api';
import type { Message, ChatSources, QueryMode } from '@/lib/types';

export interface UseChatOptions {
  conversationId?: string;
  mode?: QueryMode;
  language?: 'ka' | 'en';
  onError?: (error: Error) => void;
  onSuccess?: () => void;
}

export interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: Error | null;
  conversationId: string | null;
  mode: QueryMode;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  setMode: (mode: QueryMode) => void;
  setLanguage: (language: 'ka' | 'en') => void;
}

/**
 * Hook for managing chat state and interactions
 */
export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(
    options.conversationId || null
  );
  const [mode, setMode] = useState<QueryMode>(
    options.mode || 'auto'
  );
  const [language, setLanguage] = useState<'ka' | 'en'>(
    options.language || 'ka'
  );

  /**
   * Send a message and get response
   */
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const userMessage: Message = {
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        // Send to API
        const response = await APIClient.chat({
          message: content,
          mode,
          conversation_id: conversationId || undefined,
          language,
        });

        // Update conversation ID if new
        if (!conversationId) {
          setConversationId(response.conversation_id);
        }

        // Add assistant message with mode_used
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.answer,
          timestamp: new Date().toISOString(),
          sources: response.sources,
          mode_used: response.mode_used,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Call success callback if provided (e.g., to refresh usage)
        if (options.onSuccess) {
          options.onSuccess();
        }
      } catch (err) {
        const errorObj = err instanceof Error ? err : new Error('Unknown error');
        setError(errorObj);

        // Call error callback if provided
        if (options.onError) {
          options.onError(errorObj);
        }

        // Remove the optimistic user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, mode, language, options]
  );

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    conversationId,
    mode,
    sendMessage,
    clearMessages,
    setMode,
    setLanguage,
  };
}
