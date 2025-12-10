"""
Main orchestrator service that coordinates all legal AI operations
"""
import re
import time
from typing import Optional

from app.core import get_logger
from app.models import (
    CitedArticle,
    DisputeCase,
    QueryMode,
    ResponseSources,
    UnifiedResponse,
)
from app.services.dispute_service import DisputeService
from app.services.tax_service import TaxCodeService

logger = get_logger(__name__)


class Orchestrator:
    """
    Main orchestrator that routes queries to appropriate services

    Handles multi-mode query routing including:
    - Tax Code queries
    - Dispute case queries
    - Document generation (Phase 3)
    - Automatic mode classification
    """

    # Georgian keyword patterns for mode classification
    TAX_KEYWORDS = [
        "მუხლი",  # article
        "კოდექსი",  # code
        "განაკვეთი",  # rate
        "გადასახადი",  # tax
        "დღგ",  # VAT
        "საშემოსავლო",  # income
        "მოგება",  # profit
        "საგადასახადო კოდექსი",  # tax code
    ]

    DISPUTE_KEYWORDS = [
        "დოკუმენტის #",  # document #
        "დავების საბჭო",  # disputes council
        "ფინანსთა სამინისტრო",  # ministry of finance
        "ფინანსთა სამინისტროს დავის გადაწყვეტილება",  # ministry decision
        "საჩივარი",  # complaint/appeal
        "დავის საგანი",  # dispute subject
        "დარიცხული თანხა",  # assessed amount
        "გასაჩივრებული",  # appealed
        "სადავო საკითხი",  # disputed issue
        "საბჭოს დასკვნა",  # council's conclusion
    ]

    DOCUMENT_KEYWORDS = [
        "ხელშეკრულება",  # contract
        "დოკუმენტი",  # document
        "შაბლონი",  # template
    ]

    def __init__(
        self,
        tax_service: Optional[TaxCodeService] = None,
        dispute_service: Optional[DisputeService] = None,
        # document_service will be added in Phase 3
    ):
        """
        Initialize orchestrator with service instances

        Args:
            tax_service: Tax code service instance
            dispute_service: Dispute service instance
        """
        self.tax_service = tax_service
        self.dispute_service = dispute_service
        self.document_service = None  # Phase 3

        logger.info("Orchestrator initialized")

    async def route_query(
        self,
        message: str,
        mode: QueryMode,
        conversation_id: Optional[str] = None,
        filters: Optional[dict] = None
    ) -> UnifiedResponse:
        """
        Route query to appropriate service based on mode

        Args:
            message: User's question/message
            mode: Query mode (tax, dispute, document, auto)
            conversation_id: Optional conversation ID for context
            filters: Optional filters for search

        Returns:
            UnifiedResponse with answer, sources, and metadata

        Raises:
            ValueError: If mode is unsupported or service not available
        """
        start_time = time.time()

        # Auto-classify if mode is AUTO
        if mode == QueryMode.AUTO:
            mode = await self.auto_classify(message)
            logger.info(f"Auto-classified query as: {mode}")

        # Route to appropriate service
        try:
            if mode == QueryMode.TAX:
                response = await self._route_to_tax(message, conversation_id)
            elif mode == QueryMode.DISPUTE:
                response = await self._route_to_dispute(message, filters)
            elif mode == QueryMode.DOCUMENT:
                raise ValueError("Document mode not yet implemented (Phase 3)")
            else:
                raise ValueError(f"Unsupported mode: {mode}")

            # Add processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            response.processing_time_ms = processing_time_ms

            return response

        except Exception as e:
            logger.error(f"Error routing query: {e}", exc_info=True)
            raise

    async def _route_to_tax(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> UnifiedResponse:
        """Route query to tax service"""
        if not self.tax_service:
            raise ValueError("Tax service not available")

        logger.info("Routing to tax service")

        # Query tax service
        tax_response = await self.tax_service.query(
            question=message,
            conversation_history=[]  # TODO: Add conversation history support
        )

        # Convert to unified response
        return UnifiedResponse(
            answer=tax_response.answer,
            mode_used=QueryMode.TAX,
            sources=ResponseSources(
                tax_articles=[
                    CitedArticle(
                        article_number=article.article_number,
                        title=article.title,
                        snippet=article.snippet
                    )
                    for article in tax_response.cited_articles
                ],
                cases=[],
                templates=[]
            ),
            citations_verified=len(tax_response.cited_articles) > 0,
            warnings=self._check_tax_warnings(tax_response.cited_articles),
            processing_time_ms=0  # Will be set by route_query
        )

    async def _route_to_dispute(
        self,
        message: str,
        filters: Optional[dict] = None
    ) -> UnifiedResponse:
        """Route query to dispute service"""
        if not self.dispute_service:
            raise ValueError("Dispute service not available")

        logger.info("Routing to dispute service")

        # Query dispute service
        dispute_response = await self.dispute_service.query(
            question=message,
            filters=None,  # TODO: Convert dict to DisputeFilters if needed
            top_k=5
        )

        # Convert to unified response
        return UnifiedResponse(
            answer=dispute_response.answer,
            mode_used=QueryMode.DISPUTE,
            sources=ResponseSources(
                tax_articles=[],
                cases=[
                    DisputeCase(
                        doc_number=case.get("doc_number"),
                        date=case.get("date"),
                        category=case.get("category"),
                        decision_type=case.get("decision_type"),
                        snippet=case.get("text", "")[:200] + "..." if case.get("text") else None
                    )
                    for case in dispute_response.cases
                ],
                templates=[]
            ),
            citations_verified=len(dispute_response.cases) > 0,
            warnings=[],
            processing_time_ms=0  # Will be set by route_query
        )

    async def auto_classify(self, message: str) -> QueryMode:
        """
        Automatically classify query intent using keyword matching

        Classification logic:
        1. Check for dispute-specific keywords (highest priority)
        2. Check for document-specific keywords
        3. Default to TAX mode

        Args:
            message: User's message

        Returns:
            Classified QueryMode
        """
        message_lower = message.lower()

        # Count keyword matches for each mode
        dispute_matches = sum(
            1 for keyword in self.DISPUTE_KEYWORDS
            if keyword.lower() in message_lower
        )

        document_matches = sum(
            1 for keyword in self.DOCUMENT_KEYWORDS
            if keyword.lower() in message_lower
        )

        tax_matches = sum(
            1 for keyword in self.TAX_KEYWORDS
            if keyword.lower() in message_lower
        )

        # Classify based on highest match count
        # Dispute has priority if there's a tie
        if dispute_matches > 0 and dispute_matches >= tax_matches:
            logger.info(
                f"Classified as DISPUTE ({dispute_matches} matches): {self._get_matched_keywords(message, self.DISPUTE_KEYWORDS)}"
            )
            return QueryMode.DISPUTE

        if document_matches > 0:
            logger.info(
                f"Classified as DOCUMENT ({document_matches} matches): {self._get_matched_keywords(message, self.DOCUMENT_KEYWORDS)}"
            )
            return QueryMode.DOCUMENT

        if tax_matches > 0:
            logger.info(
                f"Classified as TAX ({tax_matches} matches): {self._get_matched_keywords(message, self.TAX_KEYWORDS)}"
            )
            return QueryMode.TAX

        # Default to TAX if no keywords match
        logger.info("No keywords matched, defaulting to TAX mode")
        return QueryMode.TAX

    def _get_matched_keywords(self, message: str, keywords: list[str]) -> list[str]:
        """Helper to get list of matched keywords"""
        message_lower = message.lower()
        return [kw for kw in keywords if kw.lower() in message_lower]

    def _check_tax_warnings(self, cited_articles: list) -> list[str]:
        """Check for warnings in tax citations"""
        warnings = []

        # Check for invalid article numbers
        invalid_citations = [
            article.article_number
            for article in cited_articles
            if not article.article_number.replace(".", "").replace("-", "").replace("ა", "").replace("ბ", "").isdigit()
            or (article.article_number.isdigit() and int(article.article_number) > 309)
        ]

        if invalid_citations:
            warnings.append(
                f"Some citations may be invalid: {invalid_citations}"
            )

        return warnings

    def get_status(self) -> dict:
        """
        Get aggregated status from all services

        Returns:
            Dictionary with service statuses
        """
        status = {
            "orchestrator": "healthy",
            "services": {}
        }

        # Tax service status
        if self.tax_service:
            try:
                # Check if tax service is initialized
                is_initialized = hasattr(self.tax_service, "_initialized") and self.tax_service._initialized
                status["services"]["tax"] = {
                    "status": "healthy" if is_initialized else "initializing",
                    "available": True
                }
            except Exception as e:
                status["services"]["tax"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "available": False
                }
        else:
            status["services"]["tax"] = {
                "status": "unavailable",
                "available": False
            }

        # Dispute service status
        if self.dispute_service:
            try:
                # Check if dispute service is initialized
                is_initialized = hasattr(self.dispute_service, "_initialized") and self.dispute_service._initialized
                status["services"]["dispute"] = {
                    "status": "healthy" if is_initialized else "initializing",
                    "available": True
                }
            except Exception as e:
                status["services"]["dispute"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "available": False
                }
        else:
            status["services"]["dispute"] = {
                "status": "unavailable",
                "available": False
            }

        # Document service status (Phase 3)
        status["services"]["document"] = {
            "status": "not_implemented",
            "available": False,
            "note": "Phase 3 feature"
        }

        # Overall health check
        unhealthy_services = [
            name for name, svc in status["services"].items()
            if svc["status"] in ["unhealthy", "unavailable"]
        ]

        if len(unhealthy_services) == len(status["services"]):
            status["orchestrator"] = "unhealthy"
        elif unhealthy_services:
            status["orchestrator"] = "degraded"

        return status
