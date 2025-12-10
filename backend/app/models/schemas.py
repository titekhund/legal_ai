"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Query Mode Enum
# ============================================================================


class QueryMode(str, Enum):
    """Query routing modes"""

    TAX = "tax"
    DISPUTE = "dispute"
    DOCUMENT = "document"  # Phase 3
    AUTO = "auto"


# ============================================================================
# Tax Code Schemas
# ============================================================================


class CitedArticle(BaseModel):
    """Citation to a specific article in the tax code"""

    article_number: str = Field(
        ...,
        description="Article number (e.g., '168.1.ა', '168', '168-ე მუხლი')"
    )
    title: Optional[str] = Field(
        None,
        description="Article title if available"
    )
    snippet: Optional[str] = Field(
        None,
        description="Relevant excerpt from the article"
    )


class Citation(BaseModel):
    """Detailed citation extracted from text"""

    raw_text: str = Field(
        ...,
        description="Original text matched in the document"
    )
    article: str = Field(
        ...,
        description="Normalized article number"
    )
    clause: Optional[str] = Field(
        None,
        description="Clause/part number (ნაწილი)"
    )
    letter: Optional[str] = Field(
        None,
        description="Letter designation (პუნქტი)"
    )
    is_valid: bool = Field(
        ...,
        description="Whether citation was found in article index"
    )
    matsne_url: Optional[str] = Field(
        None,
        description="Link to matsne.gov.ge if constructable"
    )


class TaxResponse(BaseModel):
    """Response from tax code query"""

    answer: str = Field(
        ...,
        description="Generated answer to the tax question"
    )
    cited_articles: List[CitedArticle] = Field(
        default_factory=list,
        description="List of cited articles from the tax code"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) based on citation availability"
    )
    model_used: str = Field(
        ...,
        description="Name of the LLM model used"
    )
    processing_time_ms: int = Field(
        ...,
        description="Processing time in milliseconds"
    )


# ============================================================================
# Chat Schemas
# ============================================================================


class ChatMessage(BaseModel):
    """Single chat message"""

    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        ...,
        description="Message content"
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO timestamp of the message"
    )


class ChatRequest(BaseModel):
    """Request to chat endpoint"""

    message: str = Field(
        ...,
        min_length=1,
        description="User's message/question"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID for multi-turn conversations"
    )
    conversation_history: Optional[List[ChatMessage]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint"""

    response: str = Field(
        ...,
        description="Assistant's response"
    )
    cited_articles: List[CitedArticle] = Field(
        default_factory=list,
        description="List of cited articles"
    )
    conversation_id: str = Field(
        ...,
        description="Conversation ID"
    )
    confidence: Optional[float] = Field(
        None,
        description="Confidence score if applicable"
    )
    model_used: Optional[str] = Field(
        None,
        description="Model used for generation"
    )


# ============================================================================
# Conversation Management Schemas
# ============================================================================


class Conversation(BaseModel):
    """Conversation metadata"""

    conversation_id: str = Field(
        ...,
        description="Unique conversation identifier"
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp of creation"
    )
    updated_at: str = Field(
        ...,
        description="ISO timestamp of last update"
    )
    message_count: int = Field(
        ...,
        description="Number of messages in conversation"
    )
    title: Optional[str] = Field(
        None,
        description="Auto-generated or user-provided title"
    )


class ConversationList(BaseModel):
    """List of conversations"""

    conversations: List[Conversation] = Field(
        default_factory=list,
        description="List of conversations"
    )
    total: int = Field(
        ...,
        description="Total number of conversations"
    )


class ConversationDetail(BaseModel):
    """Detailed conversation with messages"""

    conversation_id: str = Field(
        ...,
        description="Unique conversation identifier"
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp of creation"
    )
    updated_at: str = Field(
        ...,
        description="ISO timestamp of last update"
    )
    title: Optional[str] = Field(
        None,
        description="Conversation title"
    )
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation messages"
    )


# ============================================================================
# Health and Status Schemas
# ============================================================================


class ServiceStatus(BaseModel):
    """Service status information"""

    service: str = Field(
        ...,
        description="Service name"
    )
    status: str = Field(
        ...,
        description="Status: 'healthy', 'degraded', 'unhealthy'"
    )
    details: Optional[dict] = Field(
        None,
        description="Additional status details"
    )


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str = Field(
        ...,
        description="Overall status: 'healthy', 'degraded', 'unhealthy'"
    )
    services: List[ServiceStatus] = Field(
        default_factory=list,
        description="Status of individual services"
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp of health check"
    )


# ============================================================================
# Dispute Schemas
# ============================================================================


class DisputeCase(BaseModel):
    """Dispute case from Ministry of Finance decisions"""

    doc_number: Optional[str] = Field(
        None,
        description="Document number (e.g., 'ТД-2024-123')"
    )
    date: Optional[str] = Field(
        None,
        description="Decision date"
    )
    category: Optional[str] = Field(
        None,
        description="Dispute category (e.g., 'დღგ', 'საშემოსავლო გადასახადი')"
    )
    decision_type: Optional[str] = Field(
        None,
        description="Decision type: 'satisfied', 'rejected', 'partially_satisfied'"
    )
    snippet: Optional[str] = Field(
        None,
        description="Relevant excerpt from the decision"
    )


# ============================================================================
# Document Generation Schemas (Phase 3)
# ============================================================================


class DocumentType(BaseModel):
    """Document type definition"""

    id: str = Field(
        ...,
        description="Document type ID (e.g., 'nda', 'employment_contract')"
    )
    name_ka: str = Field(
        ...,
        description="Georgian name"
    )
    name_en: str = Field(
        ...,
        description="English name"
    )
    description_ka: str = Field(
        ...,
        description="Georgian description"
    )
    description_en: Optional[str] = Field(
        None,
        description="English description"
    )
    required_fields: List[str] = Field(
        default_factory=list,
        description="Required variable names"
    )
    optional_fields: List[str] = Field(
        default_factory=list,
        description="Optional variable names"
    )


class TemplateVariable(BaseModel):
    """Variable definition in template"""

    name: str = Field(
        ...,
        description="Variable name (snake_case)"
    )
    label_ka: str = Field(
        ...,
        description="Georgian label for UI"
    )
    label_en: str = Field(
        ...,
        description="English label for UI"
    )
    type: str = Field(
        ...,
        description="Variable type: 'text', 'date', 'number', 'choice', 'boolean'"
    )
    required: bool = Field(
        default=True,
        description="Whether variable is required"
    )
    default: Optional[str] = Field(
        None,
        description="Default value if not provided"
    )
    choices: Optional[List[str]] = Field(
        None,
        description="Available choices for 'choice' type"
    )
    placeholder_ka: Optional[str] = Field(
        None,
        description="Georgian placeholder text"
    )
    placeholder_en: Optional[str] = Field(
        None,
        description="English placeholder text"
    )
    validation_pattern: Optional[str] = Field(
        None,
        description="Regex pattern for validation"
    )


class DocumentTemplate(BaseModel):
    """Complete document template"""

    id: str = Field(
        ...,
        description="Template identifier"
    )
    type: str = Field(
        ...,
        description="Document type ID"
    )
    name_ka: str = Field(
        ...,
        description="Georgian template name"
    )
    name_en: str = Field(
        ...,
        description="English template name"
    )
    language: str = Field(
        ...,
        description="Template language: 'ka' or 'en'"
    )
    content: str = Field(
        ...,
        description="Template content with {{variable}} placeholders"
    )
    variables: List[TemplateVariable] = Field(
        default_factory=list,
        description="Template variables"
    )
    related_articles: List[str] = Field(
        default_factory=list,
        description="Related tax code articles"
    )
    category: Optional[str] = Field(
        None,
        description="Template category"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Search tags"
    )


class DocumentGenerationRequest(BaseModel):
    """Request to generate a document"""

    document_type: str = Field(
        ...,
        description="Document type ID"
    )
    variables: Dict[str, Any] = Field(
        ...,
        description="Variable values for template"
    )
    language: str = Field(
        default="ka",
        description="Output language: 'ka' or 'en'"
    )
    include_legal_references: bool = Field(
        default=True,
        description="Include relevant tax code article references"
    )
    template_id: Optional[str] = Field(
        None,
        description="Specific template ID to use (optional)"
    )
    format: str = Field(
        default="markdown",
        description="Output format: 'markdown', 'html', or 'plain'"
    )


class GeneratedDocument(BaseModel):
    """Generated document response"""

    content: str = Field(
        ...,
        description="Generated document content"
    )
    document_type: str = Field(
        ...,
        description="Document type that was generated"
    )
    template_used: str = Field(
        ...,
        description="Template ID that was used"
    )
    cited_articles: List[str] = Field(
        default_factory=list,
        description="Tax code articles referenced"
    )
    variables_used: Dict[str, Any] = Field(
        ...,
        description="Variables and their values"
    )
    disclaimer: str = Field(
        ...,
        description="Legal disclaimer"
    )
    format: str = Field(
        default="markdown",
        description="Document format"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of generation"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings about the generation"
    )


# ============================================================================
# Unified Response Schemas (Multi-Mode Orchestrator)
# ============================================================================


class ResponseSources(BaseModel):
    """Aggregated sources from all modes"""

    tax_articles: List[CitedArticle] = Field(
        default_factory=list,
        description="Tax code articles cited"
    )
    cases: List[DisputeCase] = Field(
        default_factory=list,
        description="Dispute cases referenced"
    )
    templates: List[DocumentTemplate] = Field(
        default_factory=list,
        description="Document templates (Phase 3)"
    )


class UnifiedResponse(BaseModel):
    """Unified response from orchestrator across all modes"""

    answer: str = Field(
        ...,
        description="Generated answer"
    )
    mode_used: QueryMode = Field(
        ...,
        description="Mode used to answer the query"
    )
    sources: ResponseSources = Field(
        default_factory=ResponseSources,
        description="All sources used in the response"
    )
    citations_verified: bool = Field(
        ...,
        description="Whether citations were verified"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings or notices"
    )
    processing_time_ms: int = Field(
        ...,
        description="Total processing time in milliseconds"
    )


# ============================================================================
# Error Response Schema
# ============================================================================


class ErrorResponse(BaseModel):
    """Error response"""

    error: dict = Field(
        ...,
        description="Error details"
    )
