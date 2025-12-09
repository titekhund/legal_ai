/**
 * API client for Legal AI backend
 */

import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  ConversationSummary,
  ServiceStatus,
  APIError,
} from './types';

// Get API base URL from environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 */
export class APIClientError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code?: string,
    public details?: Record<string, any>,
    public requestId?: string
  ) {
    super(message);
    this.name = 'APIClientError';
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // Get request ID from response headers
    const requestId = response.headers.get('X-Request-ID') || undefined;

    if (!response.ok) {
      // Try to parse error response
      let errorData: APIError | null = null;
      try {
        errorData = await response.json();
      } catch {
        // If JSON parsing fails, throw generic error
        throw new APIClientError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          undefined,
          undefined,
          requestId
        );
      }

      throw new APIClientError(
        errorData?.error?.message || 'An error occurred',
        response.status,
        errorData?.error?.code,
        errorData?.error?.details,
        requestId
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof APIClientError) {
      throw error;
    }

    // Network or other errors
    throw new APIClientError(
      error instanceof Error ? error.message : 'Network error',
      0
    );
  }
}

/**
 * API client class
 */
export class APIClient {
  /**
   * Health check endpoint
   */
  static async health(): Promise<{ status: string; timestamp: string }> {
    return fetchAPI('/health');
  }

  /**
   * Get service status
   */
  static async getStatus(): Promise<ServiceStatus> {
    return fetchAPI('/v1/status');
  }

  /**
   * Send chat message
   */
  static async chat(request: ChatRequest): Promise<ChatResponse> {
    return fetchAPI('/v1/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * List conversations
   */
  static async listConversations(
    limit: number = 100,
    offset: number = 0
  ): Promise<{ conversations: ConversationSummary[]; total: number }> {
    return fetchAPI(`/v1/conversations?limit=${limit}&offset=${offset}`);
  }

  /**
   * Get conversation by ID
   */
  static async getConversation(conversationId: string): Promise<Conversation> {
    return fetchAPI(`/v1/conversations/${conversationId}`);
  }

  /**
   * Create new conversation
   */
  static async createConversation(): Promise<{ conversation_id: string }> {
    return fetchAPI('/v1/conversations', {
      method: 'POST',
    });
  }

  /**
   * Delete conversation
   */
  static async deleteConversation(conversationId: string): Promise<void> {
    return fetchAPI(`/v1/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  }
}

/**
 * Default export for convenience
 */
export default APIClient;
