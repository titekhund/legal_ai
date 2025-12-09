/**
 * useConversations hook for managing conversation list
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import APIClient, { APIClientError } from '@/lib/api';
import type { ConversationSummary, Conversation } from '@/lib/types';

export interface UseConversationsOptions {
  autoLoad?: boolean;
  limit?: number;
}

export interface UseConversationsReturn {
  conversations: ConversationSummary[];
  isLoading: boolean;
  error: Error | null;
  total: number;
  loadConversations: () => Promise<void>;
  getConversation: (id: string) => Promise<Conversation | null>;
  createConversation: () => Promise<string | null>;
  deleteConversation: (id: string) => Promise<boolean>;
  refresh: () => Promise<void>;
}

/**
 * Hook for managing conversations
 */
export function useConversations(
  options: UseConversationsOptions = {}
): UseConversationsReturn {
  const { autoLoad = true, limit = 100 } = options;

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [total, setTotal] = useState(0);

  /**
   * Load conversations from API
   */
  const loadConversations = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await APIClient.listConversations(limit, 0);
      setConversations(response.conversations);
      setTotal(response.total);
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error('Unknown error');
      setError(errorObj);
      console.error('Failed to load conversations:', errorObj);
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  /**
   * Get a specific conversation by ID
   */
  const getConversation = useCallback(async (id: string): Promise<Conversation | null> => {
    try {
      const conversation = await APIClient.getConversation(id);
      return conversation;
    } catch (err) {
      console.error('Failed to get conversation:', err);
      return null;
    }
  }, []);

  /**
   * Create a new conversation
   */
  const createConversation = useCallback(async (): Promise<string | null> => {
    try {
      const response = await APIClient.createConversation();
      await loadConversations(); // Refresh list
      return response.conversation_id;
    } catch (err) {
      console.error('Failed to create conversation:', err);
      return null;
    }
  }, [loadConversations]);

  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await APIClient.deleteConversation(id);
        // Remove from local state
        setConversations((prev) =>
          prev.filter((conv) => conv.conversation_id !== id)
        );
        setTotal((prev) => prev - 1);
        return true;
      } catch (err) {
        console.error('Failed to delete conversation:', err);
        return false;
      }
    },
    []
  );

  /**
   * Refresh conversations
   */
  const refresh = useCallback(async () => {
    await loadConversations();
  }, [loadConversations]);

  // Auto-load on mount if enabled
  useEffect(() => {
    if (autoLoad) {
      loadConversations();
    }
  }, [autoLoad, loadConversations]);

  return {
    conversations,
    isLoading,
    error,
    total,
    loadConversations,
    getConversation,
    createConversation,
    deleteConversation,
    refresh,
  };
}
