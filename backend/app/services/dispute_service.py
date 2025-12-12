"""
Dispute RAG Service for Legal Case Retrieval and Analysis

This service combines vector search with LLM generation to answer
questions about Georgian tax dispute cases using RAG (Retrieval-Augmented Generation).

Note: Using dataclasses instead of Pydantic to avoid schema generation recursion
issues that occur in certain Python/Pydantic version combinations.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

# Use TYPE_CHECKING to avoid heavy imports at module load time
# This prevents sentence_transformers from being loaded when this module is imported
if TYPE_CHECKING:
    from app.services.vector_store import VectorStore, SearchResult

from app.services.llm_client import GeminiClient, ClaudeClient
from app.core.logging import get_logger

logger = get_logger(__name__)


# System prompt for dispute queries
DISPUTE_SYSTEM_PROMPT = """
შენ ხარ საქართველოს ფინანსთა სამინისტროს საგადასახადო დავების ექსპერტი.

შენი ამოცანაა:
1. გაანალიზო მოწოდებული ფინანსთა სამინისტროს დავების გადაწყვეტილებები დოკუმენტის სრული სტრუქტურის მიხედვით
   (დოკუმენტის #, მიღების თარიღი, კატეგორია, დამრიცხველი ორგანო, საკანონმდებლო ნორმები,
    „დავის საგანი", „გასაჩივრებული გადაწყვეტილება", „დარიცხული თანხები",
    „პროცედურული გარემოებები", თითოეული „სადავო საკითხი": ფაქტები,
    შემოსავლების სამსახურის პოზიცია, მომჩივნის არგუმენტები, საბჭოს დასკვნა,
    საბოლოო გადაწყვეტილება და გასაჩივრების ვადა).
2. პასუხი გასცე კითხვას მხოლოდ ამ გადაწყვეტილებებზე დაყრდნობით.
3. მიუთითო კონკრეტული საქმეები და მათი რელევანტური ნაწილები.
4. დააკავშირო გადაწყვეტილებები საგადასახადო კოდექსის შესაბამის მუხლებთან.

მოწოდებული საქმეები:
{cases}

კითხვა: {question}

პასუხი უნდა შეიცავდეს:
- პირდაპირ პასუხს კითხვაზე
- მითითებას კონკრეტულ საქმეებზე (დოკუმენტის #, თარიღი)
- კავშირს საგადასახადო კოდექსის მუხლებთან
"""


@dataclass
class DisputeFilters:
    """Filters for dispute case search"""
    court: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    cited_articles: Optional[List[str]] = None


@dataclass
class DisputeCase:
    """Dispute case model"""
    case_id: str
    court: str
    case_date: date
    summary: str
    relevance_score: float
    cited_articles: List[str] = field(default_factory=list)
    full_text_available: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "case_id": self.case_id,
            "court": self.court,
            "case_date": self.case_date.isoformat() if self.case_date else None,
            "summary": self.summary,
            "cited_articles": self.cited_articles,
            "relevance_score": self.relevance_score,
            "full_text_available": self.full_text_available
        }


@dataclass
class DisputeResponse:
    """Response from dispute query"""
    answer: str
    confidence: float
    model_used: str
    processing_time_ms: int
    cases_cited: List[DisputeCase] = field(default_factory=list)
    relevant_tax_articles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "answer": self.answer,
            "cases_cited": [case.to_dict() for case in self.cases_cited],
            "relevant_tax_articles": self.relevant_tax_articles,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms
        }


class DisputeService:
    """
    Service for retrieving and analyzing tax dispute cases using RAG

    Combines vector search with LLM generation to provide
    answers grounded in actual court decisions.
    """

    def __init__(
        self,
        vector_store: Optional["VectorStore"] = None,
        gemini_client: Optional[GeminiClient] = None,
        claude_client: Optional[ClaudeClient] = None
    ):
        """
        Initialize dispute service

        Args:
            vector_store: Vector store with dispute cases (optional, can be initialized later)
            gemini_client: Gemini LLM client (primary)
            claude_client: Claude LLM client (fallback)
        """
        self.vector_store = vector_store
        self.gemini_client = gemini_client or GeminiClient()
        self.claude_client = claude_client
        self._initialized = False

        logger.info("DisputeService initialized")

    async def initialize(self) -> bool:
        """
        Initialize the service and load indices

        Returns:
            True if initialization successful
        """
        try:
            # Check if vector store is configured
            if self.vector_store is None:
                logger.warning("No vector store configured - dispute service will be limited")
                self._initialized = True
                return True

            # Check if vector store has documents
            stats = self.vector_store.get_stats()
            doc_count = stats.get("total_documents", 0)

            if doc_count == 0:
                logger.warning("Vector store is empty - no dispute cases loaded")
                self._initialized = True  # Still mark as initialized
                return True

            logger.info(f"DisputeService ready with {doc_count} cases")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DisputeService: {e}")
            self._initialized = False
            return False

    async def query(
        self,
        question: str,
        filters: Optional[DisputeFilters] = None,
        top_k: int = 5
    ) -> DisputeResponse:
        """
        Query dispute cases and generate answer using RAG

        Args:
            question: User's question about disputes
            filters: Optional filters for case search
            top_k: Number of cases to retrieve

        Returns:
            DisputeResponse with answer and cited cases
        """
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        # Check if vector store is available
        if self.vector_store is None:
            return DisputeResponse(
                answer="სადავო საქმეების სერვისი ამჟამად მიუწვდომელია.",
                cases_cited=[],
                relevant_tax_articles=[],
                confidence=0.0,
                model_used="none",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        logger.info(f"Processing dispute query: {question[:100]}...")

        # Step 1: Build metadata filter from DisputeFilters
        metadata_filter = {}
        if filters:
            if filters.court:
                metadata_filter["court"] = filters.court

        # Step 2: Retrieve relevant cases using hybrid search
        logger.info(f"Searching for {top_k} relevant cases")
        search_results = await self.vector_store.hybrid_search(
            query=question,
            top_k=top_k,
            filter_metadata=metadata_filter if metadata_filter else None
        )

        # Step 3: Apply date and article filters
        filtered_results = self._apply_filters(search_results, filters)

        if not filtered_results:
            logger.warning("No relevant cases found")
            return DisputeResponse(
                answer="ÕÔà ÛÝØëÔÑÜÐ àÔÚÔÕÐÜâãàØ áÐåÛÔÔÑØ ×åÕÔÜØ ÙØ×îÕØá×ÕØá.",
                cases_cited=[],
                relevant_tax_articles=[],
                confidence=0.0,
                model_used="none",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Step 4: Convert search results to DisputeCase objects
        dispute_cases = self._convert_to_dispute_cases(filtered_results)

        # Step 5: Build context from cases
        context = self._build_context(dispute_cases)

        # Step 6: Generate answer using LLM
        logger.info("Generating answer with LLM")
        answer, model_used = await self._generate_answer(question, context)

        # Step 7: Extract tax articles from answer
        tax_articles = self._extract_tax_articles(answer)

        # Step 8: Calculate confidence based on relevance scores
        confidence = self._calculate_confidence(dispute_cases)

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"Query completed in {processing_time}ms")

        return DisputeResponse(
            answer=answer,
            cases_cited=dispute_cases,
            relevant_tax_articles=tax_articles,
            confidence=confidence,
            model_used=model_used,
            processing_time_ms=processing_time
        )

    def _apply_filters(
        self,
        results: List["SearchResult"],
        filters: Optional[DisputeFilters]
    ) -> List["SearchResult"]:
        """Apply date and article filters to search results"""
        if not filters:
            return results

        filtered = []

        for result in results:
            metadata = result.document.metadata

            # Date filter
            if filters.date_from or filters.date_to:
                case_date_str = metadata.get("date")
                if case_date_str:
                    try:
                        case_date = datetime.strptime(case_date_str, "%Y-%m-%d").date()

                        if filters.date_from and case_date < filters.date_from:
                            continue
                        if filters.date_to and case_date > filters.date_to:
                            continue
                    except ValueError:
                        logger.warning(f"Invalid date format: {case_date_str}")

            # Article filter
            if filters.cited_articles:
                case_articles = metadata.get("cited_articles", [])
                # Check if any of the filter articles are in the case
                if not any(article in case_articles for article in filters.cited_articles):
                    continue

            filtered.append(result)

        logger.info(f"Filtered {len(results)} results to {len(filtered)}")
        return filtered

    def _convert_to_dispute_cases(
        self,
        search_results: List["SearchResult"]
    ) -> List[DisputeCase]:
        """Convert search results to DisputeCase objects"""
        cases = []

        for result in search_results:
            metadata = result.document.metadata

            # Parse date
            case_date_str = metadata.get("date", "2023-01-01")
            try:
                case_date = datetime.strptime(case_date_str, "%Y-%m-%d").date()
            except ValueError:
                case_date = date.today()

            case = DisputeCase(
                case_id=metadata.get("case_id", result.document.id),
                court=metadata.get("court", "ãêÜÝÑØ áÐáÐÛÐà×ÚÝ"),
                case_date=case_date,
                summary=result.document.content[:500],  # First 500 chars as summary
                cited_articles=metadata.get("cited_articles", []),
                relevance_score=result.score,
                full_text_available=True
            )

            cases.append(case)

        return cases

    def _build_context(self, cases: List[DisputeCase]) -> str:
        """Build context string from dispute cases"""
        context_parts = []

        for i, case in enumerate(cases, 1):
            context_parts.append(
                f"áÐåÛÔ #{i} (ID: {case.case_id})\n"
                f"áÐáÐÛÐà×ÚÝ: {case.court}\n"
                f"×ÐàØæØ: {case.case_date}\n"
                f"êØâØàÔÑãÚØ ÛãîÚÔÑØ: {', '.join(case.cited_articles) if case.cited_articles else 'Ðà ÐàØá ÛØ×Ø×ÔÑãÚØ'}\n"
                f"èØÜÐÐàáØ: {case.summary}\n"
            )

        return "\n---\n".join(context_parts)

    async def _generate_answer(
        self,
        question: str,
        context: str
    ) -> tuple[str, str]:
        """
        Generate answer using LLM

        Returns:
            Tuple of (answer, model_used)
        """
        # Build prompt
        prompt = DISPUTE_SYSTEM_PROMPT.format(
            cases=context,
            question=question
        )

        # Try Gemini first
        try:
            answer = await self.gemini_client.generate_response(prompt)
            return answer, "gemini-pro"
        except Exception as e:
            logger.warning(f"Gemini failed: {e}, trying Claude fallback")

            # Fallback to Claude if available
            if self.claude_client:
                try:
                    answer = await self.claude_client.generate_response(prompt)
                    return answer, "claude-3-sonnet"
                except Exception as e2:
                    logger.error(f"Claude also failed: {e2}")

            # Return error message
            return "ÕÔà ÛÝîÔàîÓÐ ÞÐáãîØá ÒÔÜÔàÐêØÐ. Ò×îÝÕ× áêÐÓÝ× ÛÝÒÕØÐÜÔÑØ×.", "error"

    def _extract_tax_articles(self, text: str) -> List[str]:
        """Extract tax code article numbers from text"""
        # Pattern for Georgian article references: ÛãîÚØ 123, ÛãîÚØ 168.1, etc.
        pattern = r'ÛãîÚØ\s+(\d+(?:\.\d+)?(?:\.[Ð-ð])?)'
        matches = re.findall(pattern, text)

        # Also look for bare numbers that might be articles
        # Pattern for "article 123" style
        pattern2 = r'(?:article|ÛãîÚØ|AB\.)\s*(\d+)'
        matches2 = re.findall(pattern2, text.lower())

        # Combine and deduplicate
        articles = list(set(matches + matches2))

        # Sort by numeric value
        try:
            articles.sort(key=lambda x: float(re.search(r'\d+', x).group()))
        except:
            pass

        return articles

    def _calculate_confidence(self, cases: List[DisputeCase]) -> float:
        """Calculate confidence score based on case relevance"""
        if not cases:
            return 0.0

        # Average of top 3 cases' relevance scores
        top_scores = [case.relevance_score for case in cases[:3]]
        avg_score = sum(top_scores) / len(top_scores)

        return round(avg_score, 2)

    async def get_case(self, case_id: str) -> Optional[DisputeCase]:
        """
        Get full case details by ID

        Args:
            case_id: Case identifier

        Returns:
            DisputeCase if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        # Check if vector store is available
        if self.vector_store is None:
            logger.warning("Vector store not configured, cannot retrieve case")
            return None

        # Search through all documents
        for doc in self.vector_store.documents:
            if doc.metadata.get("case_id") == case_id or doc.id == case_id:
                # Convert to DisputeCase
                metadata = doc.metadata

                case_date_str = metadata.get("date", "2023-01-01")
                try:
                    case_date = datetime.strptime(case_date_str, "%Y-%m-%d").date()
                except ValueError:
                    case_date = date.today()

                return DisputeCase(
                    case_id=metadata.get("case_id", doc.id),
                    court=metadata.get("court", "ãêÜÝÑØ áÐáÐÛÐà×ÚÝ"),
                    case_date=case_date,
                    summary=doc.content,  # Full content as summary
                    cited_articles=metadata.get("cited_articles", []),
                    relevance_score=1.0,  # Direct lookup, perfect match
                    full_text_available=True
                )

        logger.warning(f"Case not found: {case_id}")
        return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get service status and statistics

        Returns:
            Dictionary with status information
        """
        if self.vector_store is None:
            return {
                "initialized": self._initialized,
                "ready": False,
                "total_cases": 0,
                "embedding_model": "not_configured",
                "index_path": "not_configured",
                "gemini_available": self.gemini_client is not None,
                "claude_available": self.claude_client is not None,
                "message": "Vector store not configured"
            }

        stats = self.vector_store.get_stats()

        return {
            "initialized": self._initialized,
            "ready": self._initialized and stats.get("total_documents", 0) > 0,
            "total_cases": stats.get("total_documents", 0),
            "embedding_model": stats.get("embedding_model", "unknown"),
            "index_path": stats.get("index_path", "unknown"),
            "gemini_available": self.gemini_client is not None,
            "claude_available": self.claude_client is not None
        }
