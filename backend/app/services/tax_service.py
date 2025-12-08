"""
Tax code service for Georgian Tax Code reasoning (Container 1)
"""
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from app.core import (
    ConfigurationError,
    LLMError,
    TaxCodeNotFoundError,
    get_logger,
    get_settings,
)
from app.models.schemas import CitedArticle, TaxResponse
from app.services.llm_client import GeminiClient

from .prompts import TAX_SYSTEM_PROMPT

logger = get_logger(__name__)


class TaxCodeService:
    """
    Service for querying Georgian Tax Code using Gemini with file context

    This implements Container 1 - NotebookLM-style reasoning over the tax code.
    """

    # Maximum conversation history to keep (to manage token usage)
    MAX_HISTORY_MESSAGES = 10

    def __init__(self, llm_client: Optional[GeminiClient] = None):
        """
        Initialize TaxCodeService

        Args:
            llm_client: Optional GeminiClient instance (creates new if not provided)
        """
        self.settings = get_settings()
        self.llm_client = llm_client or GeminiClient()

        # File management
        self.tax_code_path = Path(self.settings.tax_code_path)
        self.uploaded_file: Optional[Any] = None
        self.file_upload_status = "not_initialized"

        logger.info("TaxCodeService initialized")

    async def initialize(self) -> bool:
        """
        Initialize the service by uploading the tax code PDF

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not self.tax_code_path.exists():
                logger.error(f"Tax code file not found at: {self.tax_code_path}")
                self.file_upload_status = "file_not_found"
                raise TaxCodeNotFoundError(
                    message=f"Tax code file not found at: {self.tax_code_path}",
                    details={"path": str(self.tax_code_path)}
                )

            logger.info(f"Uploading tax code PDF: {self.tax_code_path}")
            self.file_upload_status = "uploading"

            # Upload file to Gemini File API
            # Note: The GeminiClient handles caching internally
            self.uploaded_file = genai.upload_file(str(self.tax_code_path))

            logger.info(
                f"Tax code uploaded successfully: {self.uploaded_file.name}"
            )
            self.file_upload_status = "ready"

            return True

        except TaxCodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize TaxCodeService: {e}")
            self.file_upload_status = "error"
            raise ConfigurationError(
                message=f"Failed to initialize tax code service: {str(e)}",
                details={"error": str(e)}
            )

    def _extract_citations(self, text: str) -> List[CitedArticle]:
        """
        Extract Georgian legal citations from text

        Patterns supported:
        - "მუხლი 168"
        - "მუხლი 168, ნაწილი 1"
        - "მუხლი 168.1.ა"
        - "168-ე მუხლი"
        - "168-ე მუხლის"

        Args:
            text: Text to extract citations from

        Returns:
            List of CitedArticle objects
        """
        citations = []
        seen_articles = set()

        # Pattern 1: "მუხლი X" or "მუხლი X.Y.Z"
        pattern1 = r'მუხლი\s+(\d+(?:\.\d+)?(?:\.[ა-ჰ])?)'
        for match in re.finditer(pattern1, text):
            article_num = match.group(1)
            if article_num not in seen_articles:
                citations.append(CitedArticle(
                    article_number=article_num,
                    title=None,
                    snippet=None
                ))
                seen_articles.add(article_num)

        # Pattern 2: "X-ე მუხლი" or "X-ე მუხლის"
        pattern2 = r'(\d+)-ე\s+მუხლ[ი|ის]'
        for match in re.finditer(pattern2, text):
            article_num = match.group(1)
            if article_num not in seen_articles:
                citations.append(CitedArticle(
                    article_number=article_num,
                    title=None,
                    snippet=None
                ))
                seen_articles.add(article_num)

        # Pattern 3: Complex citations like "მუხლი 168, ნაწილი 1, პუნქტი ა"
        pattern3 = r'მუხლი\s+(\d+),\s*ნაწილი\s+(\d+)(?:,\s*პუნქტი\s+([ა-ჰ]))?'
        for match in re.finditer(pattern3, text):
            article_num = match.group(1)
            part_num = match.group(2)
            point = match.group(3)

            if point:
                full_ref = f"{article_num}.{part_num}.{point}"
            else:
                full_ref = f"{article_num}.{part_num}"

            if full_ref not in seen_articles:
                citations.append(CitedArticle(
                    article_number=full_ref,
                    title=None,
                    snippet=None
                ))
                seen_articles.add(full_ref)

        logger.info(f"Extracted {len(citations)} citations from response")
        return citations

    def _calculate_confidence(self, citations: List[CitedArticle]) -> float:
        """
        Calculate confidence score based on number of citations

        Args:
            citations: List of citations

        Returns:
            Confidence score (0-1)
        """
        if len(citations) == 0:
            return 0.3  # Low confidence if no citations
        elif len(citations) == 1:
            return 0.6  # Medium confidence with one citation
        elif len(citations) == 2:
            return 0.8  # High confidence with two citations
        else:
            return 0.95  # Very high confidence with multiple citations

    def _format_conversation_history(
        self,
        history: List[Dict[str, str]]
    ) -> str:
        """
        Format conversation history for context

        Args:
            history: List of message dictionaries with 'role' and 'content'

        Returns:
            Formatted history string
        """
        if not history:
            return ""

        # Limit to last N messages
        recent_history = history[-self.MAX_HISTORY_MESSAGES:]

        formatted = "წინა საუბრის კონტექსტი:\n\n"
        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                formatted += f"კითხვა: {content}\n"
            else:
                formatted += f"პასუხი: {content}\n"
            formatted += "\n"

        formatted += "---\n\n"
        return formatted

    async def query(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> TaxResponse:
        """
        Query the Georgian Tax Code

        Args:
            question: User's question in Georgian
            conversation_history: Optional previous conversation messages

        Returns:
            TaxResponse with answer and citations

        Raises:
            LLMError: If query fails
            ConfigurationError: If service not initialized
        """
        start_time = time.time()

        # Check if initialized
        if self.file_upload_status != "ready" or self.uploaded_file is None:
            logger.error("TaxCodeService not initialized")
            raise ConfigurationError(
                message="Tax code service not initialized. Call initialize() first.",
                details={"status": self.file_upload_status}
            )

        try:
            # Format conversation context if provided
            context = ""
            if conversation_history:
                context = self._format_conversation_history(conversation_history)

            # Prepare the full prompt
            full_prompt = f"{TAX_SYSTEM_PROMPT}\n\n"
            if context:
                full_prompt += f"{context}\n"
            full_prompt += f"კითხვა: {question}"

            logger.info(f"Querying tax code with question length: {len(question)}")

            # Generate response with file context
            response_text = await self.llm_client.generate_with_file(
                prompt=full_prompt,
                file_ref=self.uploaded_file
            )

            # Extract citations from response
            citations = self._extract_citations(response_text)

            # Calculate confidence
            confidence = self._calculate_confidence(citations)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Tax code query completed in {processing_time_ms}ms "
                f"with {len(citations)} citations"
            )

            return TaxResponse(
                answer=response_text,
                cited_articles=citations,
                confidence=confidence,
                model_used=self.llm_client.get_model_name(),
                processing_time_ms=processing_time_ms
            )

        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Error querying tax code: {e}")
            raise LLMError(
                message=f"Failed to query tax code: {str(e)}",
                details={"error": str(e)}
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get service status information

        Returns:
            Dictionary with status information
        """
        return {
            "service": "TaxCodeService",
            "file_upload_status": self.file_upload_status,
            "tax_code_path": str(self.tax_code_path),
            "file_exists": self.tax_code_path.exists(),
            "uploaded_file_name": self.uploaded_file.name if self.uploaded_file else None,
            "model_name": self.llm_client.get_model_name(),
            "max_history_messages": self.MAX_HISTORY_MESSAGES,
        }

    async def health_check(self) -> bool:
        """
        Perform health check

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Check if file exists
            if not self.tax_code_path.exists():
                logger.warning(f"Health check failed: file not found at {self.tax_code_path}")
                return False

            # Check if file is uploaded
            if self.file_upload_status != "ready":
                logger.warning(f"Health check failed: file status is {self.file_upload_status}")
                return False

            # Check if LLM client is working
            if not self.llm_client:
                logger.warning("Health check failed: LLM client not initialized")
                return False

            logger.info("TaxCodeService health check passed")
            return True

        except Exception as e:
            logger.error(f"Health check failed with error: {e}")
            return False
