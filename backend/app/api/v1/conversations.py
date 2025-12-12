"""
Conversation management endpoints
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.core import get_logger
from app.db.models import User
from app.storage import get_conversation_store

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class ConversationMessage(BaseModel):
    """Conversation message"""

    role: str
    content: str
    timestamp: str


class ConversationSummary(BaseModel):
    """Conversation summary"""

    conversation_id: str
    created_at: str
    updated_at: str
    message_count: int
    expires_at: str


class ConversationDetail(BaseModel):
    """Full conversation details"""

    conversation_id: str
    created_at: str
    updated_at: str
    expires_at: str
    messages: List[ConversationMessage]


class ConversationListResponse(BaseModel):
    """List of conversations"""

    conversations: List[ConversationSummary]
    total: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """
    List all active conversations

    **Requires authentication**

    Args:
        limit: Maximum number of conversations to return (default: 100)
        offset: Offset for pagination (default: 0)

    Returns:
        List of conversation summaries
    """
    conversation_store = get_conversation_store()

    summaries = conversation_store.list_conversations(limit=limit, offset=offset)

    return ConversationListResponse(
        conversations=[
            ConversationSummary(**summary) for summary in summaries
        ],
        total=len(summaries)
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific conversation with full message history

    **Requires authentication**

    Args:
        conversation_id: Conversation ID

    Returns:
        Full conversation details

    Raises:
        HTTPException: 404 if conversation not found
    """
    conversation_store = get_conversation_store()

    conversation = conversation_store.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found or expired"
        )

    return ConversationDetail(
        conversation_id=conversation["conversation_id"],
        created_at=conversation["created_at"].isoformat() + "Z",
        updated_at=conversation["updated_at"].isoformat() + "Z",
        expires_at=conversation["expires_at"].isoformat() + "Z",
        messages=[
            ConversationMessage(**msg) for msg in conversation["messages"]
        ]
    )


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    current_user: User = Depends(get_current_user),
):
    """
    Create a new conversation

    **Requires authentication**

    Returns:
        New conversation ID
    """
    conversation_store = get_conversation_store()

    conversation_id = conversation_store.create_conversation()

    return {
        "conversation_id": conversation_id,
        "message": "Conversation created successfully"
    }


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a conversation

    **Requires authentication**

    Args:
        conversation_id: Conversation ID

    Raises:
        HTTPException: 404 if conversation not found
    """
    conversation_store = get_conversation_store()

    deleted = conversation_store.delete_conversation(conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # FastAPI automatically returns 204 No Content with no body
    return None


@router.get("/conversations/stats", response_model=dict)
async def get_conversation_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Get conversation storage statistics

    **Requires authentication**

    Returns:
        Storage statistics
    """
    conversation_store = get_conversation_store()

    return conversation_store.get_stats()
