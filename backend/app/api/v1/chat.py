"""
Chat API endpoints for legal AI assistant
"""
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core import LLMError, get_logger
from app.models import CitedArticle
from app.services import TaxCodeService
from app.storage import get_conversation_store

logger = get_logger(__name__)
router = APIRouter()

# Global service instance (will be set from main.py)
_tax_service: Optional[TaxCodeService] = None


def set_tax_service(service: TaxCodeService):
    """Set the tax service instance"""
    global _tax_service
    _tax_service = service


def get_tax_service() -> TaxCodeService:
    """Get the tax service instance"""
    return _tax_service


# ============================================================================
# Request/Response Models
# ============================================================================


class ChatRequest(BaseModel):
    """Chat request"""

    message: str = Field(..., min_length=1, description="User's message")
    mode: str = Field("tax", description="Mode: 'tax' (Phase 1 only)")
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
async def chat(request: ChatRequest):
    """
    Chat endpoint for legal AI assistant

    Currently supports:
    - Tax mode: Georgian Tax Code queries

    Args:
        request: Chat request with message and options

    Returns:
        Chat response with answer, sources, and metadata

    Raises:
        HTTPException: If service not available or error occurs
    """
    start_time = time.time()

    # Validate mode
    if request.mode not in ["tax"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{request.mode}'. Only 'tax' is supported in Phase 1."
        )

    # Get services
    tax_service = get_tax_service()
    if not tax_service:
        raise HTTPException(
            status_code=503,
            detail="Tax service not initialized"
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

    # Get conversation history
    messages = conversation_store.get_messages(conversation_id)

    # Convert to format expected by tax service
    history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
    ]

    try:
        # Query tax service
        logger.info(f"Processing tax query for conversation {conversation_id}")

        tax_response = await tax_service.query(
            question=request.message,
            conversation_history=history
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
            content=tax_response.answer
        )

        # Convert cited articles to sources
        tax_sources = [
            ChatSource(
                article_number=article.article_number,
                title=article.title,
                snippet=article.snippet
            )
            for article in tax_response.cited_articles
        ]

        # Check for warnings
        warnings = []
        invalid_citations = [
            article for article in tax_response.cited_articles
            if not article.article_number.isdigit() or int(article.article_number) > 309
        ]
        if invalid_citations:
            warnings.append(
                f"Some citations may be invalid: {[a.article_number for a in invalid_citations]}"
            )

        # Calculate total processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        return ChatResponse(
            answer=tax_response.answer,
            mode_used="tax",
            sources=ChatSources(
                tax_articles=tax_sources,
                cases=[],  # Empty for Phase 1
                templates=[]  # Empty for Phase 1
            ),
            citations_verified=len(tax_response.cited_articles) > 0,
            warnings=warnings,
            conversation_id=conversation_id,
            processing_time_ms=processing_time_ms
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
