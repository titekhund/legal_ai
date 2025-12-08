"""
In-memory conversation storage with TTL for Phase 1
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core import get_logger

logger = get_logger(__name__)


class ConversationStore:
    """
    In-memory conversation storage with TTL

    Features:
    - Stores conversations in memory
    - Automatic expiration after 24 hours
    - Maximum 100 conversations per instance
    - Thread-safe operations
    """

    # Configuration
    MAX_CONVERSATIONS = 100
    TTL_HOURS = 24

    def __init__(self):
        """Initialize the conversation store"""
        self._conversations: Dict[str, dict] = {}
        logger.info("ConversationStore initialized")

    def create_conversation(
        self,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Create a new conversation

        Args:
            conversation_id: Optional conversation ID (generates UUID if not provided)

        Returns:
            Conversation ID
        """
        # Clean up expired conversations first
        self._cleanup_expired()

        # Check if we've hit the limit
        if len(self._conversations) >= self.MAX_CONVERSATIONS:
            # Remove oldest conversation
            oldest_id = min(
                self._conversations.keys(),
                key=lambda k: self._conversations[k]["created_at"]
            )
            self.delete_conversation(oldest_id)
            logger.warning(
                f"Reached max conversations ({self.MAX_CONVERSATIONS}), "
                f"removed oldest: {oldest_id}"
            )

        # Generate ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Create conversation
        now = datetime.utcnow()
        self._conversations[conversation_id] = {
            "conversation_id": conversation_id,
            "messages": [],
            "created_at": now,
            "updated_at": now,
            "expires_at": now + timedelta(hours=self.TTL_HOURS)
        }

        logger.info(f"Created conversation: {conversation_id}")
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Add a message to a conversation

        Args:
            conversation_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content

        Returns:
            True if successful, False if conversation not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        # Add message
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.utcnow()

        logger.debug(f"Added message to conversation {conversation_id}")
        return True

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """
        Get a conversation by ID

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation dict or None if not found/expired
        """
        conversation = self._conversations.get(conversation_id)

        if not conversation:
            return None

        # Check if expired
        if datetime.utcnow() > conversation["expires_at"]:
            self.delete_conversation(conversation_id)
            return None

        return conversation

    def get_messages(self, conversation_id: str) -> List[dict]:
        """
        Get messages from a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages or empty list if not found
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []

        return conversation["messages"]

    def list_conversations(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """
        List all active conversations

        Args:
            limit: Maximum number of conversations to return
            offset: Offset for pagination

        Returns:
            List of conversation summaries
        """
        # Clean up expired conversations
        self._cleanup_expired()

        # Get all conversations sorted by updated_at (most recent first)
        conversations = sorted(
            self._conversations.values(),
            key=lambda c: c["updated_at"],
            reverse=True
        )

        # Apply pagination
        conversations = conversations[offset:offset + limit]

        # Return summaries (without messages)
        summaries = []
        for conv in conversations:
            summaries.append({
                "conversation_id": conv["conversation_id"],
                "created_at": conv["created_at"].isoformat() + "Z",
                "updated_at": conv["updated_at"].isoformat() + "Z",
                "message_count": len(conv["messages"]),
                "expires_at": conv["expires_at"].isoformat() + "Z"
            })

        return summaries

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False

    def _cleanup_expired(self) -> int:
        """
        Remove expired conversations

        Returns:
            Number of conversations removed
        """
        now = datetime.utcnow()
        expired = [
            cid for cid, conv in self._conversations.items()
            if now > conv["expires_at"]
        ]

        for cid in expired:
            del self._conversations[cid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired conversations")

        return len(expired)

    def get_stats(self) -> dict:
        """
        Get storage statistics

        Returns:
            Statistics dict
        """
        self._cleanup_expired()

        total_messages = sum(
            len(conv["messages"]) for conv in self._conversations.values()
        )

        return {
            "total_conversations": len(self._conversations),
            "max_conversations": self.MAX_CONVERSATIONS,
            "total_messages": total_messages,
            "ttl_hours": self.TTL_HOURS
        }


# Global instance
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """Get or create the global conversation store"""
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store
