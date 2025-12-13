"""
Chat API endpoints for legal AI assistant
"""
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core import LLMError, get_logger
from app.db import get_async_session, User
from app.models import CitedArticle, QueryMode
from app.services import AuthService, Orchestrator, TaxCodeService
from app.storage import get_conversation_store

logger = get_logger(__name__)
router = APIRouter()

# Global service instances (will be set from main.py)
_tax_service: Optional[TaxCodeService] = None
_orchestrator: Optional[Orchestrator] = None


def set_tax_service(service: TaxCodeService):
    """Set the tax service instance"""
    global _tax_service
    _tax_service = service


def get_tax_service() -> TaxCodeService:
    """Get the tax service instance"""
    return _tax_service


def set_orchestrator(orchestrator: Orchestrator):
    """Set the orchestrator instance"""
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator() -> Orchestrator:
    """Get the orchestrator instance"""
    return _orchestrator


# ============================================================================
# Request/Response Models
# ============================================================================


class ChatRequest(BaseModel):
    """Chat request"""

    message: str = Field(..., min_length=1, description="User's message")
    mode: str = Field("auto", description="Mode: 'tax', 'dispute', 'document', 'auto'")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    language: str = Field("ka", description="Language: 'ka' (Georgian) or 'en' (English)")


class ChatSource(BaseModel):
    """Source information"""

    article_number: str
    title: Optional[str] = None
    snippet: Optional[str] = None


class ChatSources(BaseModel):
    """All sources used"""

    tax_articles: List[ChatSource] = Field(default_factory=list)
    cases: List[dict] = Field(default_factory=list, description="Empty for Phase 1")
    templates: List[dict] = Field(default_factory=list, description="Empty for Phase 1")


class ChatResponse(BaseModel):
    """Chat response"""

    answer: str
    mode_used: str
    sources: ChatSources
    citations_verified: bool
    warnings: List[str] = Field(default_factory=list)
    conversation_id: str
    processing_time_ms: int


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Chat endpoint for legal AI assistant

    **Requires authentication** - Include JWT token in Authorization header.

    Supports multiple modes:
    - Tax mode: Georgian Tax Code queries
    - Dispute mode: Ministry of Finance dispute decisions
    - Document mode: Document generation (Phase 3)
    - Auto mode: Automatic mode detection based on query content

    Args:
        request: Chat request with message and options

    Returns:
        Chat response with answer, sources, and metadata

    Raises:
        HTTPException: If service not available, usage limit exceeded, or error occurs
    """
    start_time = time.time()

    # Validate mode first (cheap check before usage increment)
    valid_modes = ["tax", "dispute", "document", "auto"]
    if request.mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{request.mode}'. Must be one of: {valid_modes}"
        )

    # Atomically check and increment usage (prevents race conditions)
    # Increment happens BEFORE LLM call to prevent abuse via request flooding
    auth_service = AuthService(session)
    is_allowed, reason, updated_user = await auth_service.check_and_increment_usage(
        user_id=str(current_user.id),
        endpoint="/v1/chat",
        request_type=request.mode,
    )
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "USAGE_LIMIT_EXCEEDED",
                "message": reason,
                "usage": {
                    "daily_used": updated_user.daily_requests_count if updated_user else 0,
                    "monthly_used": updated_user.monthly_requests_count if updated_user else 0,
                }
            }
        )

    # Get orchestrator
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator not initialized"
        )

    conversation_store = get_conversation_store()

    # Get or create conversation
    conversation_id = request.conversation_id
    if conversation_id:
        # Verify conversation exists
        if not conversation_store.get_conversation(conversation_id):
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )
    else:
        # Create new conversation
        conversation_id = conversation_store.create_conversation()

    try:
        # Route query through orchestrator
        logger.info(f"Processing {request.mode} query for conversation {conversation_id}")

        # Convert mode string to QueryMode enum
        try:
            mode = QueryMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode: {request.mode}"
            )

        # Route query
        unified_response = await orchestrator.route_query(
            message=request.message,
            mode=mode,
            conversation_id=conversation_id,
            filters=None  # TODO: Add filters support
        )

        # Save messages to conversation
        conversation_store.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message
        )
        conversation_store.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=unified_response.answer
        )

        # Convert unified response to chat response format
        tax_sources = [
            ChatSource(
                article_number=article.article_number,
                title=article.title,
                snippet=article.snippet
            )
            for article in unified_response.sources.tax_articles
        ]

        case_sources = [
            {
                "doc_number": case.doc_number,
                "date": case.date,
                "category": case.category,
                "decision_type": case.decision_type,
                "snippet": case.snippet
            }
            for case in unified_response.sources.cases
        ]

        # Usage was already incremented atomically at request start
        return ChatResponse(
            answer=unified_response.answer,
            mode_used=unified_response.mode_used.value,
            sources=ChatSources(
                tax_articles=tax_sources,
                cases=case_sources,
                templates=[]  # Phase 3
            ),
            citations_verified=unified_response.citations_verified,
            warnings=unified_response.warnings,
            conversation_id=conversation_id,
            processing_time_ms=unified_response.processing_time_ms
        )

    except LLMError as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
