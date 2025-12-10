/**
 * TypeScript type definitions for Legal AI application
 */

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface ChatRequest {
  message: string;
  mode?: 'tax' | 'dispute' | 'document' | 'auto';
  conversation_id?: string;
  language?: 'ka' | 'en';
}

export interface ChatResponse {
  answer: string;
  mode_used: string;
  sources: ChatSources;
  citations_verified: boolean;
  conversation_id: string;
  model_used?: string;
  processing_time_ms?: number;
  warnings?: string[];
}

export interface ChatSources {
  tax_articles: TaxArticle[];
  cases: DisputeCase[];
  templates: any[];
}

export interface TaxArticle {
  article: string;
  title: string;
  content: string;
  relevance_score: number;
  matsne_url?: string;
}

export interface DisputeCase {
  doc_number?: string;
  date?: string;
  category?: string;
  decision_type?: string;
  snippet?: string;
}

export interface Conversation {
  conversation_id: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ConversationSummary {
  conversation_id: string;
  message_count: number;
  last_message_preview: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: ChatSources;
  mode_used?: string;
}

export type QueryMode = 'tax' | 'dispute' | 'document' | 'auto';

// ============================================================================
// Component Props Types
// ============================================================================

export interface MessageBubbleProps {
  message: Message;
  isUser: boolean;
}

export interface CitationPanelProps {
  sources: ChatSources;
  isOpen: boolean;
  onToggle: () => void;
}

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

// ============================================================================
// API Error Types
// ============================================================================

export interface APIError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  request_id?: string;
}

// ============================================================================
// Service Status Types
// ============================================================================

export interface ServiceStatus {
  status: string;
  timestamp: string;
  tax_service?: {
    ready: boolean;
    model?: string;
    file_uploaded?: boolean;
  };
  dispute_service?: {
    ready: boolean;
    message?: string;
  };
  document_service?: {
    ready: boolean;
    message?: string;
  };
}
