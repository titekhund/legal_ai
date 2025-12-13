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
  AuthResponse,
  User,
  UsageInfo,
  RegisterRequest,
  LoginRequest,
} from './types';

// Get API base URL from environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Default request timeout (30 seconds)
const DEFAULT_TIMEOUT = 30000;

// Auth token storage key
const AUTH_TOKEN_KEY = 'legal_ai_auth_token';
const AUTH_USER_KEY = 'legal_ai_auth_user';

/**
 * Get stored auth token
 */
export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Get stored user data
 */
export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userJson = localStorage.getItem(AUTH_USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

/**
 * Store auth data
 */
export function storeAuthData(token: string, user: User): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

/**
 * Clear auth data
 */
export function clearAuthData(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

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
 * Create an AbortSignal with timeout
 */
function createTimeoutSignal(timeout: number): AbortSignal {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), timeout);
  return controller.signal;
}

/**
 * Generic fetch wrapper with error handling and timeout
 */
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {},
  timeout: number = DEFAULT_TIMEOUT,
  includeAuth: boolean = false
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  // Build headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  // Add auth token if requested
  if (includeAuth) {
    const token = getStoredToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || createTimeoutSignal(timeout),
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

    // Handle timeout errors
    if (error instanceof Error && error.name === 'AbortError') {
      throw new APIClientError(
        'Request timeout - please try again',
        408,
        'TIMEOUT_ERROR'
      );
    }

    // Network or other errors
    throw new APIClientError(
      error instanceof Error ? error.message : 'Network error',
      0,
      'NETWORK_ERROR'
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

  // ========================================================================
  // Authentication
  // ========================================================================

  /**
   * Register a new user
   */
  static async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await fetchAPI<AuthResponse>('/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    storeAuthData(response.access_token, response.user);
    return response;
  }

  /**
   * Login user
   */
  static async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await fetchAPI<AuthResponse>('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    storeAuthData(response.access_token, response.user);
    return response;
  }

  /**
   * Logout user (client-side only)
   */
  static logout(): void {
    clearAuthData();
  }

  /**
   * Get current user info
   */
  static async getCurrentUser(): Promise<User> {
    return fetchAPI('/v1/auth/me', {}, DEFAULT_TIMEOUT, true);
  }

  /**
   * Get current user's usage info
   */
  static async getUsageInfo(): Promise<UsageInfo> {
    return fetchAPI('/v1/auth/usage', {}, DEFAULT_TIMEOUT, true);
  }

  /**
   * Refresh auth token
   */
  static async refreshToken(): Promise<AuthResponse> {
    const response = await fetchAPI<AuthResponse>(
      '/v1/auth/refresh',
      { method: 'POST' },
      DEFAULT_TIMEOUT,
      true
    );
    storeAuthData(response.access_token, response.user);
    return response;
  }

  // ========================================================================
  // Chat (requires authentication)
  // ========================================================================

  /**
   * Send chat message
   */
  static async chat(request: ChatRequest): Promise<ChatResponse> {
    return fetchAPI('/v1/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    }, DEFAULT_TIMEOUT, true);
  }

  // ========================================================================
  // Conversations
  // ========================================================================

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
